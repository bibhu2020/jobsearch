import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import axios from 'axios';
import { ApplySettingsService } from '../apply/apply-settings.service';
import { exchangeCode, frontendBase, googleAuthUrl, googleConfigured, readIdToken } from '../auth/google-oauth';

const GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'openid', 'email'];

@Injectable()
export class IntegrationsService {
  constructor(private jwt: JwtService, private settings: ApplySettingsService) {}

  private get redirectUri() {
    return process.env.GOOGLE_OAUTH_REDIRECT_URI || 'http://localhost:3000/api/integrations/gmail/callback';
  }

  frontendBase(): string {
    return frontendBase();
  }

  gmailAuthUrl(userId: number, email?: string): string {
    if (!googleConfigured()) {
      throw new ServiceUnavailableException('Gmail connection is not configured on this server');
    }
    const state = this.jwt.sign({ sub: userId, purpose: 'gmail' }, { expiresIn: '10m' });
    return googleAuthUrl({
      redirect_uri: this.redirectUri,
      scope: GMAIL_SCOPES.join(' '),
      access_type: 'offline',
      prompt: 'consent',
      include_granted_scopes: 'true',
      ...(email ? { login_hint: email } : {}),
      state,
    });
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
      const data = await exchangeCode(code, this.redirectUri);
      if (!data.refresh_token) return false;
      const email = data.id_token ? readIdToken(data.id_token).email : null;
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
}
