import {
  BadGatewayException, BadRequestException, HttpException, HttpStatus, Injectable, NotFoundException,
  OnApplicationBootstrap, OnModuleDestroy,
} from '@nestjs/common';
import axios from 'axios';
import { randomUUID } from 'crypto';
import { readFileSync } from 'fs';
import { extname } from 'path';
import { DatabaseService } from '../database/database.service';
import { CryptoService } from '../crypto/crypto.service';
import { ApplySettingsService } from './apply-settings.service';

export const TERMINAL_STATUSES = ['submitted', 'failed', 'cancelled'];
const CONTROL_ACTIONS = ['resume', 'submit', 'cancel', 'mark-applied', 'finish-login'];
const POLL_INTERVAL_MS = 3000;
const EASY_APPLY_SPACING_MIN = 3;
const MAX_POLL_FAILURES = 40; // ~2 min of the agents service being unreachable

// Abuse / capacity limits. Every user's browser runs share one container and one outbound IP.
const envInt = (name: string, fallback: number) => {
  const n = parseInt(process.env[name] ?? '', 10);
  return Number.isFinite(n) && n >= 0 ? n : fallback;
};
const USER_DAILY_LIMIT = envInt('APPLY_USER_DAILY_LIMIT', 25);          // runs started per user per 24 h
const MAX_PENDING_RUNS = envInt('APPLY_MAX_PENDING_RUNS', 10);          // unfinished runs across all users
const EASY_APPLY_GLOBAL_DAILY_CAP = envInt('EASY_APPLY_GLOBAL_DAILY_CAP', 40); // all users, shared IP
// Every column except the screenshot bytes, which are served separately.
const RUN_COLUMNS = `id, user_id, pipeline_card_id, kind, status, site, channel, apply_url, auto_submitted,
  message, fields, started_at, finished_at, (screenshot IS NOT NULL) AS has_screenshot`;

@Injectable()
export class ApplyService implements OnApplicationBootstrap, OnModuleDestroy {
  private agentsUrl = process.env.AGENTS_URL || 'http://localhost:8000';
  private trackers = new Map<string, NodeJS.Timeout>();
  private pollFailures = new Map<string, number>();
  private starting = new Set<number>();

  constructor(
    private db: DatabaseService,
    private crypto: CryptoService,
    private settings: ApplySettingsService,
  ) {}

  // Runs after every module's onModuleInit, so the DB pool exists.
  async onApplicationBootstrap() {
    // Re-attach to runs the agents service still holds (gateway-only restart);
    // the tracker marks the rest failed when the agent answers 404.
    try {
      const open = await this.db.query<any>(
        `SELECT id, user_id, pipeline_card_id FROM application_runs
         WHERE status NOT IN ('submitted', 'failed', 'cancelled')`,
      );
      for (const r of open) this.track(r.user_id, r.pipeline_card_id, r.id);
    } catch (err: any) {
      console.warn(`apply: could not resume tracking (${err.message})`);
    }
  }

  onModuleDestroy() {
    for (const t of this.trackers.values()) clearInterval(t);
  }

  // ── Queries ──────────────────────────────────────────────────────────────────

  private parseRun(row: any) {
    return row ? { ...row, fields: row.fields ? JSON.parse(row.fields) : [] } : null;
  }

  private async getOwnedRun(userId: number, runId: string) {
    const row = await this.db.get<any>(`SELECT ${RUN_COLUMNS} FROM application_runs WHERE id = ? AND user_id = ?`, [runId, userId]);
    if (!row) throw new NotFoundException('Run not found');
    return row;
  }

  async getActiveRun(userId: number) {
    const row = await this.db.get<any>(
      `SELECT ${RUN_COLUMNS} FROM application_runs WHERE user_id = ? AND status NOT IN ('submitted', 'failed', 'cancelled')
       ORDER BY started_at DESC LIMIT 1`,
      [userId],
    );
    return this.parseRun(row);
  }

  async getCardRuns(userId: number, cardId: number) {
    const rows = await this.db.query<any>(
      `SELECT ${RUN_COLUMNS} FROM application_runs WHERE user_id = ? AND pipeline_card_id = ? ORDER BY started_at DESC LIMIT 10`,
      [userId, cardId],
    );
    return rows.map(r => this.parseRun(r));
  }

  async getScreenshot(userId: number, runId: string): Promise<Buffer> {
    const row = await this.db.get<{ screenshot: Buffer | null }>(
      'SELECT screenshot FROM application_runs WHERE id = ? AND user_id = ?',
      [runId, userId],
    );
    if (!row?.screenshot) throw new NotFoundException('No screenshot for this run');
    return row.screenshot;
  }

  /** DB state merged with the live view (screenshot, log) while the run is active. */
  async getRun(userId: number, runId: string) {
    const row = this.parseRun(await this.getOwnedRun(userId, runId));
    if (TERMINAL_STATUSES.includes(row.status)) return { ...row, live: null };
    try {
      const { data } = await axios.get(`${this.agentsUrl}/apply/runs/${runId}`, { timeout: 5000 });
      let message = data.message ?? row.message;
      if (data.status === 'queued') {
        const ahead = await this.db.get<{ n: number }>(
          `SELECT COUNT(*)::int AS n FROM application_runs WHERE status = 'queued' AND started_at < ?`,
          [row.started_at],
        );
        message = ahead?.n ? `Waiting for a free browser — ${ahead.n} application(s) ahead of yours` : 'Waiting for a free browser — you\'re next';
      }
      return {
        ...row,
        status: data.status,
        site: data.site ?? row.site,
        message,
        fields: data.fields ?? row.fields,
        live: { screenshot: data.screenshot, log: data.log, step: data.step, needs: data.needs },
      };
    } catch {
      return { ...row, live: null };
    }
  }

  // ── Start ────────────────────────────────────────────────────────────────────

  async start(userId: number, cardId: number) {
    const active = await this.getActiveRun(userId);
    if (active) return { runId: active.id, resumed: true };
    if (this.starting.has(userId)) throw new BadRequestException('An application is already starting');
    this.starting.add(userId);
    try {
      await this.enforceLimits(userId);
      return await this.startLocked(userId, cardId);
    } finally {
      this.starting.delete(userId);
    }
  }

  private async enforceLimits(userId: number) {
    const mine = await this.db.query<{ started_at: string }>(
      `SELECT started_at FROM application_runs
       WHERE user_id = ? AND kind = 'apply' AND started_at > NOW() - INTERVAL '24 hours'
       ORDER BY started_at ASC`,
      [userId],
    );
    if (mine.length >= USER_DAILY_LIMIT) {
      const next = new Date(new Date(mine[0].started_at).getTime() + 24 * 3600 * 1000);
      throw new HttpException(
        `Daily limit reached (${USER_DAILY_LIMIT} applications per 24 hours). Next one available after ${next.toLocaleString('en-US', { timeZone: 'UTC' })} UTC.`,
        HttpStatus.TOO_MANY_REQUESTS,
      );
    }
    const pending = await this.db.get<{ n: number }>(
      `SELECT COUNT(*)::int AS n FROM application_runs WHERE status NOT IN ('submitted', 'failed', 'cancelled')`,
    );
    if ((pending?.n ?? 0) >= MAX_PENDING_RUNS) {
      throw new HttpException(
        'The apply service is busy with other applications right now — please try again in a few minutes.',
        HttpStatus.TOO_MANY_REQUESTS,
      );
    }
  }

  private async startLocked(userId: number, cardId: number) {
    const card = await this.db.get<any>(
      `SELECT pc.id, pc.stage, j.title, j.company, j.location, j.description, j.url
       FROM pipeline_cards pc JOIN jobs j ON pc.job_id = j.id
       WHERE pc.id = ? AND pc.user_id = ?`,
      [cardId, userId],
    );
    if (!card) throw new NotFoundException('Card not found');
    if (card.stage !== 'wishlist') throw new BadRequestException('Only Wishlist jobs can be auto-applied');
    if (!card.url) throw new BadRequestException('This job has no posting URL to apply on');

    const user = await this.db.get<any>('SELECT email, name FROM users WHERE id = ?', [userId]);
    const profile = await this.db.get<any>('SELECT * FROM user_profiles WHERE user_id = ?', [userId]);
    const row = await this.settings.getRow(userId);
    const missing = this.settings.missingForApply(row, !!profile?.resume_path);
    if (missing.length) {
      throw new BadRequestException({ message: 'Finish your Auto-Apply setup in Profile first', missing });
    }

    // Secrets encrypted under a previous CREDENTIALS_ENC_KEY can't be read: ask for the password again,
    // and treat Gmail / site sessions as disconnected rather than failing the run.
    const password = this.tryDecrypt(row!.portal_password_enc);
    if (password === null) {
      throw new BadRequestException({
        message: 'Your saved job portal password could not be read — please enter it again in Profile',
        missing: ['Job portal password'],
      });
    }
    const gmailToken = this.tryDecrypt(row!.gmail_refresh_token_enc);
    const defaults = JSON.parse(row!.defaults || '{}');
    const resume = await this.loadResumeFile(userId, cardId, profile, defaults);
    const coverLetter = await this.db.get<any>(
      `SELECT content FROM generated_kits WHERE pipeline_card_id = ? AND type = 'cover_letter'`,
      [cardId],
    );
    const sessions = await this.db.query<any>('SELECT site, state_enc FROM user_site_sessions WHERE user_id = ?', [userId]);
    const accounts = await this.db.query<any>('SELECT tenant FROM ats_accounts WHERE user_id = ?', [userId]);

    const runId = randomUUID();
    await this.db.run(
      'INSERT INTO application_runs (id, user_id, pipeline_card_id, kind, status, apply_url) VALUES (?, ?, ?, ?, ?, ?)',
      [runId, userId, cardId, 'apply', 'queued', card.url],
    );

    const payload = {
      run_id: runId,
      kind: 'apply',
      job: { url: card.url, title: card.title, company: card.company, location: card.location, description: card.description },
      applicant: {
        email: user.email,
        password,
        name: user.name,
        defaults,
        profile: {
          summary: profile.profile_summary,
          location: profile.location,
          linkedin_url: profile.linkedin_url,
          skills: profile.skills ? JSON.parse(profile.skills) : [],
          experience: profile.experience ? JSON.parse(profile.experience) : [],
          education: profile.education ? JSON.parse(profile.education) : [],
        },
        resume_text: profile.resume_text || '',
      },
      files: { resume, cover_letter_text: coverLetter?.content || '' },
      settings: { auto_submit: row!.auto_submit },
      easy_apply: await this.easyApplyAllowance(userId, row!.easy_apply_daily_cap),
      gmail: gmailToken ? { refresh_token: gmailToken } : null,
      sessions: Object.fromEntries(
        sessions.map(s => [s.site, this.tryDecrypt(s.state_enc)] as const)
          .filter(([, state]) => state !== null)
          .map(([site, state]) => [site, JSON.parse(state!)]),
      ),
      known_accounts: accounts.map(a => a.tenant),
    };

    try {
      await axios.post(`${this.agentsUrl}/apply/runs`, payload, { timeout: 15000 });
    } catch (err: any) {
      await this.finish(runId, 'failed', `Could not reach the apply agent: ${err.message}`);
      throw new BadGatewayException('Apply agent is unavailable');
    }

    this.track(userId, cardId, runId);
    return { runId, resumed: false };
  }

  private tryDecrypt(payload: string | null): string | null {
    if (!payload) return null;
    try {
      return this.crypto.decrypt(payload);
    } catch {
      return null;
    }
  }

  /** Tailored resume kit (rendered to PDF) when present, else the uploaded resume. */
  private async loadResumeFile(userId: number, cardId: number, profile: any, defaults: any) {
    const baseName = [defaults.firstName, defaults.lastName].filter(Boolean).join('_').replace(/\s+/g, '_') || 'Resume';
    const kit = await this.db.get<any>(
      `SELECT gk.content, j.title, j.company FROM generated_kits gk
       JOIN pipeline_cards pc ON gk.pipeline_card_id = pc.id JOIN jobs j ON pc.job_id = j.id
       WHERE gk.pipeline_card_id = ? AND gk.type = 'resume' AND pc.user_id = ?`,
      [cardId, userId],
    );
    if (kit?.content?.trim()) {
      try {
        const { data } = await axios.post(
          `${this.agentsUrl}/pdf/export`,
          { content: kit.content, type: 'resume', title: kit.title, company: kit.company },
          { responseType: 'arraybuffer', timeout: 60000 },
        );
        return { filename: `${baseName}_Resume.pdf`, b64: Buffer.from(data).toString('base64'), tailored: true };
      } catch (err: any) {
        console.warn(`apply: tailored resume export failed, using uploaded resume (${err.message})`);
      }
    }

    const path: string = profile.resume_path;
    let buffer: Buffer;
    if (/^https?:\/\//.test(path)) {
      const token = process.env.GITHUB_TOKEN;
      const { data } = await axios.get(path, {
        responseType: 'arraybuffer',
        headers: token && path.includes('githubusercontent.com') ? { Authorization: `token ${token}` } : {},
      });
      buffer = Buffer.from(data);
    } else {
      buffer = readFileSync(path);
    }
    const ext = extname(path.split('?')[0]).toLowerCase() || '.pdf';
    return { filename: `${baseName}_Resume${ext}`, b64: buffer.toString('base64'), tailored: false };
  }

  private async easyApplyAllowance(userId: number, cap: number) {
    const recent = await this.db.query<any>(
      `SELECT started_at FROM application_runs
       WHERE user_id = ? AND channel = 'easy_apply' AND status = 'submitted'
         AND started_at > NOW() - INTERVAL '24 hours'
       ORDER BY started_at DESC`,
      [userId],
    );
    if (recent.length >= cap) {
      const oldest = new Date(recent[recent.length - 1].started_at);
      const next = new Date(oldest.getTime() + 24 * 3600 * 1000);
      return { allowed: false, reason: `Easy Apply limit reached (${cap}/day). Next slot after ${next.toISOString()}` };
    }
    if (recent.length) {
      const waitMs = new Date(recent[0].started_at).getTime() + EASY_APPLY_SPACING_MIN * 60000 - Date.now();
      if (waitMs > 0) {
        return { allowed: false, reason: `Easy Apply needs ${EASY_APPLY_SPACING_MIN} minutes between applications — try again in ${Math.ceil(waitMs / 60000)} min` };
      }
    }
    const global = await this.db.get<{ n: number }>(
      `SELECT COUNT(*)::int AS n FROM application_runs
       WHERE channel = 'easy_apply' AND status = 'submitted' AND started_at > NOW() - INTERVAL '24 hours'`,
    );
    if ((global?.n ?? 0) >= EASY_APPLY_GLOBAL_DAILY_CAP) {
      return { allowed: false, reason: 'Easy Apply is paused for today across the service to protect everyone\'s accounts — try again tomorrow' };
    }
    return { allowed: true, reason: '' };
  }

  // ── Control ──────────────────────────────────────────────────────────────────

  async input(userId: number, runId: string, body: any) {
    await this.getOwnedRun(userId, runId);
    const kinds = ['click', 'type', 'key', 'scroll'];
    if (!kinds.includes(body?.kind)) throw new BadRequestException('Invalid input kind');
    return this.forward(runId, 'input', body);
  }

  async provideVerification(userId: number, runId: string, value: string) {
    await this.getOwnedRun(userId, runId);
    if (typeof value !== 'string' || !value.trim() || value.length > 2000) {
      throw new BadRequestException('Enter the verification code or link');
    }
    return this.forward(runId, 'verification', { value });
  }

  async control(userId: number, runId: string, action: string) {
    if (!CONTROL_ACTIONS.includes(action)) throw new BadRequestException('Invalid action');
    const row = await this.getOwnedRun(userId, runId);
    if (TERMINAL_STATUSES.includes(row.status)) throw new BadRequestException('Run already finished');
    return this.forward(runId, action, {});
  }

  private async forward(runId: string, action: string, body: any) {
    try {
      const { data } = await axios.post(`${this.agentsUrl}/apply/runs/${runId}/${action}`, body, { timeout: 10000 });
      return data;
    } catch (err: any) {
      if (err?.response?.status === 409) throw new BadRequestException(err.response.data?.detail || 'Not allowed now');
      throw new BadGatewayException('Apply agent is unavailable');
    }
  }

  // ── Tracking ─────────────────────────────────────────────────────────────────

  private track(userId: number, cardId: number, runId: string) {
    let busy = false;
    const timer = setInterval(async () => {
      if (busy) return;
      busy = true;
      try {
        await this.poll(userId, cardId, runId);
      } catch (err: any) {
        console.warn(`apply: tracker error for ${runId}: ${err.message}`);
      } finally {
        busy = false;
      }
    }, POLL_INTERVAL_MS);
    this.trackers.set(runId, timer);
  }

  private stopTracking(runId: string) {
    const t = this.trackers.get(runId);
    if (t) clearInterval(t);
    this.trackers.delete(runId);
  }

  private async poll(userId: number, cardId: number, runId: string) {
    const exists = await this.db.get<any>('SELECT id FROM application_runs WHERE id = ?', [runId]);
    if (!exists) {
      // Card (and its runs) deleted mid-run.
      this.stopTracking(runId);
      axios.post(`${this.agentsUrl}/apply/runs/${runId}/cancel`).catch(() => {});
      return;
    }

    let data: any;
    try {
      ({ data } = await axios.get(`${this.agentsUrl}/apply/runs/${runId}?screenshot=0`, { timeout: 5000 }));
      this.pollFailures.delete(runId);
    } catch (err: any) {
      const failures = (this.pollFailures.get(runId) ?? 0) + 1;
      this.pollFailures.set(runId, failures);
      if (err?.response?.status === 404 || failures >= MAX_POLL_FAILURES) {
        this.stopTracking(runId);
        this.pollFailures.delete(runId);
        await this.finish(runId, 'failed', 'Run lost (apply service restarted or unreachable)');
      }
      return;
    }

    await this.db.run(
      `UPDATE application_runs SET status = ?, site = ?, channel = ?, apply_url = COALESCE(?, apply_url),
         auto_submitted = ?, message = ?, fields = ? WHERE id = ?`,
      [
        data.status, data.site ?? null, data.channel ?? null, data.apply_url ?? null,
        !!data.auto_submitted, data.message ?? null, JSON.stringify(data.fields ?? []), runId,
      ],
    );

    if (data.gmail_invalid) {
      // Revoked or expired (7-day tokens in Google "testing" mode): show "Connect Gmail" again.
      await this.db.run(
        'UPDATE user_apply_settings SET gmail_refresh_token_enc = NULL, gmail_email = NULL, updated_at = NOW() WHERE user_id = ? AND gmail_refresh_token_enc IS NOT NULL',
        [userId],
      );
    }

    for (const tenant of data.new_accounts ?? []) {
      await this.db.run(
        `INSERT INTO ats_accounts (user_id, tenant, email) SELECT ?, ?, email FROM users WHERE id = ?
         ON CONFLICT (user_id, tenant) DO NOTHING`,
        [userId, tenant, userId],
      );
    }
    for (const [site, state] of Object.entries(data.session_updates ?? {})) {
      await this.db.run(
        `INSERT INTO user_site_sessions (user_id, site, state_enc, updated_at) VALUES (?, ?, ?, NOW())
         ON CONFLICT (user_id, site) DO UPDATE SET state_enc = EXCLUDED.state_enc, updated_at = NOW()`,
        [userId, site, this.crypto.encrypt(JSON.stringify(state))],
      );
    }

    if (!TERMINAL_STATUSES.includes(data.status)) return;
    this.stopTracking(runId);
    await this.db.run('UPDATE application_runs SET finished_at = NOW() WHERE id = ?', [runId]);

    if (data.status === 'submitted') {
      await this.moveToApplied(userId, cardId);
      await this.saveConfirmationScreenshot(runId);
    }
  }

  private async finish(runId: string, status: string, message: string) {
    await this.db.run(
      'UPDATE application_runs SET status = ?, message = ?, finished_at = NOW() WHERE id = ?',
      [status, message, runId],
    );
  }

  private async moveToApplied(userId: number, cardId: number) {
    const { next } = (await this.db.get<any>(
      `SELECT COALESCE(MAX(position) + 1, 0) AS next FROM pipeline_cards WHERE user_id = ? AND stage = 'applied'`,
      [userId],
    )) ?? { next: 0 };
    await this.db.run(
      `UPDATE pipeline_cards SET stage = 'applied', position = ?, updated_at = NOW()
       WHERE id = ? AND user_id = ? AND stage = 'wishlist'`,
      [next, cardId, userId],
    );
  }

  /** Stored in Postgres, not GitHub storage: it shows personal answers (phone, visa, demographics). */
  private async saveConfirmationScreenshot(runId: string) {
    try {
      const { data } = await axios.get(`${this.agentsUrl}/apply/runs/${runId}`, { timeout: 5000 });
      if (!data.screenshot) return;
      await this.db.run('UPDATE application_runs SET screenshot = ? WHERE id = ?', [Buffer.from(data.screenshot, 'base64'), runId]);
    } catch (err: any) {
      console.warn(`apply: could not save confirmation screenshot (${err.message})`);
    }
  }

}
