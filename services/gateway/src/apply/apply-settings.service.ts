import { BadRequestException, Injectable } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import { CryptoService } from '../crypto/crypto.service';

export const EASY_APPLY_MAX_CAP = 5;

/** Fields that must be present before an application run can start. */
const REQUIRED_DEFAULTS = ['firstName', 'lastName', 'phone'];

export interface ApplySettingsRow {
  user_id: number;
  portal_password_enc: string | null;
  auto_submit: boolean;
  easy_apply_daily_cap: number;
  defaults: string;
  gmail_refresh_token_enc: string | null;
  gmail_email: string | null;
}

@Injectable()
export class ApplySettingsService {
  constructor(private db: DatabaseService, private crypto: CryptoService) {}

  async getRow(userId: number): Promise<ApplySettingsRow | undefined> {
    return this.db.get<ApplySettingsRow>('SELECT * FROM user_apply_settings WHERE user_id = ?', [userId]);
  }

  private async ensureRow(userId: number) {
    await this.db.run(
      'INSERT INTO user_apply_settings (user_id) VALUES (?) ON CONFLICT (user_id) DO NOTHING',
      [userId],
    );
  }

  /** Public view — never includes decrypted or encrypted secrets. */
  async getSettings(userId: number) {
    const row = await this.getRow(userId);
    const sessions = await this.db.query<{ site: string; updated_at: string }>(
      'SELECT site, updated_at FROM user_site_sessions WHERE user_id = ?',
      [userId],
    );
    const siteStatus = (site: string) => {
      const s = sessions.find(x => x.site === site);
      return { connected: !!s, updatedAt: s?.updated_at ?? null };
    };
    return {
      encryptionConfigured: this.crypto.isConfigured(),
      gmailConfigured: !!process.env.GOOGLE_OAUTH_CLIENT_ID,
      portalPasswordSet: !!row?.portal_password_enc,
      autoSubmit: row ? row.auto_submit : true,
      easyApplyDailyCap: row?.easy_apply_daily_cap ?? EASY_APPLY_MAX_CAP,
      defaults: row?.defaults ? JSON.parse(row.defaults) : {},
      gmail: { connected: !!row?.gmail_refresh_token_enc, email: row?.gmail_email ?? null },
      sites: { linkedin: siteStatus('linkedin'), dice: siteStatus('dice') },
    };
  }

  async updateSettings(userId: number, body: {
    portalPassword?: string; autoSubmit?: boolean; easyApplyDailyCap?: number; defaults?: Record<string, any>;
  }) {
    await this.ensureRow(userId);

    if (body.portalPassword !== undefined) {
      if (body.portalPassword.length < 8) throw new BadRequestException('Portal password must be at least 8 characters');
      await this.db.run(
        'UPDATE user_apply_settings SET portal_password_enc = ?, updated_at = NOW() WHERE user_id = ?',
        [this.crypto.encrypt(body.portalPassword), userId],
      );
    }

    const cap = body.easyApplyDailyCap;
    if (cap !== undefined && (!Number.isInteger(cap) || cap < 0 || cap > EASY_APPLY_MAX_CAP)) {
      throw new BadRequestException(`Easy Apply daily cap must be between 0 and ${EASY_APPLY_MAX_CAP}`);
    }

    await this.db.run(
      `UPDATE user_apply_settings SET
         auto_submit          = COALESCE(?, auto_submit),
         easy_apply_daily_cap = COALESCE(?, easy_apply_daily_cap),
         defaults             = COALESCE(?, defaults),
         updated_at           = NOW()
       WHERE user_id = ?`,
      [
        body.autoSubmit ?? null,
        cap ?? null,
        body.defaults !== undefined ? JSON.stringify(body.defaults) : null,
        userId,
      ],
    );
    return this.getSettings(userId);
  }

  async setGmail(userId: number, refreshToken: string, email: string | null) {
    await this.ensureRow(userId);
    await this.db.run(
      'UPDATE user_apply_settings SET gmail_refresh_token_enc = ?, gmail_email = ?, updated_at = NOW() WHERE user_id = ?',
      [this.crypto.encrypt(refreshToken), email, userId],
    );
  }

  async clearGmail(userId: number): Promise<string | null> {
    const row = await this.getRow(userId);
    await this.db.run(
      'UPDATE user_apply_settings SET gmail_refresh_token_enc = NULL, gmail_email = NULL, updated_at = NOW() WHERE user_id = ?',
      [userId],
    );
    if (!row?.gmail_refresh_token_enc) return null;
    try {
      return this.crypto.decrypt(row.gmail_refresh_token_enc);
    } catch {
      return null; // unreadable (key changed) — nothing to revoke
    }
  }

  /** Lists what the user still has to set up before auto-apply can run. */
  missingForApply(row: ApplySettingsRow | undefined, hasResume: boolean): string[] {
    const missing: string[] = [];
    if (!this.crypto.isConfigured()) missing.push('Server encryption key (CREDENTIALS_ENC_KEY)');
    if (!hasResume) missing.push('Resume');
    if (!row?.portal_password_enc) missing.push('Job portal password');
    const defaults = row?.defaults ? JSON.parse(row.defaults) : {};
    for (const key of REQUIRED_DEFAULTS) {
      if (!String(defaults[key] ?? '').trim()) missing.push(`Application defaults: ${key}`);
    }
    if (!Array.isArray(defaults.workAuthorizedCountries) || !defaults.workAuthorizedCountries.length) {
      missing.push('Application defaults: workAuthorizedCountries');
    }
    if (typeof defaults.requiresSponsorship !== 'boolean') {
      missing.push('Application defaults: requiresSponsorship');
    }
    return missing;
  }
}
