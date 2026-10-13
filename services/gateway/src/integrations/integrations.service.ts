import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import axios from 'axios';
import { ApplySettingsService } from '../apply/apply-settings.service';

const GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'openid', 'email'];

@Injectable()
export class IntegrationsService {
  constructor(private jwt: JwtService, private settings: ApplySettingsService) {}

  private get clientId() { return process.env.GOOGLE_OAUTH_CLIENT_ID; }
  private get clientSecret() { return process.env.GOOGLE_OAUTH_CLIENT_SECRET; }
  private get redirectUri() {
    return process.env.GOOGLE_OAUTH_REDIRECT_URI || 'http://localhost:3000/api/integrations/gmail/callback';
  }

  /** Where to send the browser after the OAuth round-trip. */
  frontendBase(): string {
    if (process.env.NODE_ENV === 'production') return '';
    return process.env.FRONTEND_URL || 'http://localhost:5173';
  }

  gmailAuthUrl(userId: number): string {
    if (!this.clientId || !this.clientSecret) {
      throw new ServiceUnavailableException('Gmail connection is not configured on this server');
    }
    const state = this.jwt.sign({ sub: userId, purpose: 'gmail' }, { expiresIn: '10m' });
    const params = new URLSearchParams({
      client_id: this.clientId,
      redirect_uri: this.redirectUri,
      response_type: 'code',
      scope: GMAIL_SCOPES.join(' '),
      access_type: 'offline',
      prompt: 'consent',
      include_granted_scopes: 'true',
      state,
    });
    return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  }

  async gmailCallback(code: string, state: string): Promise<boolean> {
    let userId: number;
    try {
      const payload = this.jwt.verify<{ sub: number; purpose: string }>(state);
      if (payload.purpose !== 'gmail') return false;
      userId = payload.sub;
    } catch {
      return false;
    }
    try {
      const { data } = await axios.post(
        'https://oauth2.googleapis.com/token',
        new URLSearchParams({
          code,
          client_id: this.clientId!,
          client_secret: this.clientSecret!,
          redirect_uri: this.redirectUri,
          grant_type: 'authorization_code',
        }),
      );
      if (!data.refresh_token) return false;
      const email = data.id_token ? this.emailFromIdToken(data.id_token) : null;
      await this.settings.setGmail(userId, data.refresh_token, email);
      return true;
    } catch (err: any) {
      console.warn(`gmail: token exchange failed (${err?.response?.data?.error || err.message})`);
      return false;
    }
  }

  async disconnectGmail(userId: number) {
    const token = await this.settings.clearGmail(userId);
    if (token) {
      axios.post('https://oauth2.googleapis.com/revoke', new URLSearchParams({ token })).catch(() => {});
    }
    return { disconnected: true };
  }

  /** id_token comes straight from Google's token endpoint over TLS, so decoding without verifying is fine. */
  private emailFromIdToken(idToken: string): string | null {
    try {
      const payload = JSON.parse(Buffer.from(idToken.split('.')[1], 'base64url').toString('utf8'));
      return payload.email ?? null;
    } catch {
      return null;
    }
  }
}
