import { Injectable, ServiceUnavailableException, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { DatabaseService } from '../database/database.service';
import { exchangeCode, googleAuthUrl, googleConfigured, readIdToken } from './google-oauth';

/** Sign-in is Google-only: Google is the identity provider and vouches for the email address. */
@Injectable()
export class AuthService {
  constructor(
    private db: DatabaseService,
    private jwt: JwtService,
  ) {}

  private get redirectUri(): string {
    if (process.env.GOOGLE_LOGIN_REDIRECT_URI) return process.env.GOOGLE_LOGIN_REDIRECT_URI;
    const gmail = process.env.GOOGLE_OAUTH_REDIRECT_URI;
    if (gmail) return gmail.replace('/api/integrations/gmail/callback', '/api/auth/google/callback');
    return 'http://localhost:3000/api/auth/google/callback';
  }

  /** Google consent URL; `nonce` is also set in a cookie and checked on return (login-CSRF protection). */
  googleLoginUrl(nonce: string): string {
    if (!googleConfigured()) throw new ServiceUnavailableException('Google sign-in is not configured on this server');
    const state = this.jwt.sign({ purpose: 'login', nonce }, { expiresIn: '10m' });
    return googleAuthUrl({
      redirect_uri: this.redirectUri,
      scope: 'openid email profile',
      prompt: 'select_account',
      state,
    });
  }

  async googleLogin(code: string, state: string, cookieNonce: string | undefined) {
    let payload: { purpose: string; nonce: string };
    try {
      payload = this.jwt.verify(state);
    } catch {
      throw new UnauthorizedException('Sign-in expired — please try again');
    }
    if (payload.purpose !== 'login' || !cookieNonce || payload.nonce !== cookieNonce) {
      throw new UnauthorizedException('Sign-in could not be verified — please try again');
    }

    const tokens = await exchangeCode(code, this.redirectUri);
    const identity = readIdToken(tokens.id_token);
    if (!identity.email || !identity.emailVerified) {
      throw new UnauthorizedException('Your Google account email is not verified');
    }

    const userId = await this.findOrCreateUser(identity.sub, identity.email, identity.name);
    return this.issueToken(userId, identity.email);
  }

  private async findOrCreateUser(sub: string, email: string, name: string | null): Promise<number> {
    const bySub = await this.db.get<{ id: number }>('SELECT id FROM users WHERE google_sub = ?', [sub]);
    if (bySub) return bySub.id;

    // Accounts created before Google sign-in are linked by (Google-verified) email.
    const byEmail = await this.db.get<{ id: number; name: string | null }>(
      'SELECT id, name FROM users WHERE LOWER(email) = ?', [email],
    );
    if (byEmail) {
      await this.db.run(
        'UPDATE users SET google_sub = ?, name = COALESCE(name, ?) WHERE id = ?',
        [sub, name, byEmail.id],
      );
      return byEmail.id;
    }

    // password_hash is NOT NULL in the schema; '!' can never match a bcrypt hash.
    const userId = await this.db.insert(
      'INSERT INTO users (name, email, password_hash, google_sub) VALUES (?, ?, ?, ?)',
      [name, email, '!', sub],
    );
    await this.db.run('INSERT INTO user_profiles (user_id) VALUES (?)', [userId]);
    return userId;
  }

  private issueToken(userId: number, email: string) {
    const token = this.jwt.sign({ sub: userId, email });
    return { token, user: { id: userId, email } };
  }
}
