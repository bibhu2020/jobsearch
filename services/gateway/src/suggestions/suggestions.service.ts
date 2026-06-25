import { Injectable } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import axios from 'axios';

@Injectable()
export class SuggestionsService {
  private agentsUrl = process.env.AGENTS_URL || 'http://localhost:8000';

  constructor(private db: DatabaseService) {}

  async getSuggestions(userId: number) {
    const rows = await this.db.query<any>(
      "SELECT * FROM job_suggestions WHERE user_id = ? AND status = 'pending' AND match_score >= 70 ORDER BY match_score DESC, created_at DESC",
      [userId],
    );
    return rows.map(r => ({
      ...r,
      matching: r.matching ? JSON.parse(r.matching) : [],
      gaps:     r.gaps     ? JSON.parse(r.gaps)     : [],
    }));
  }

  async importFromFiles(userId: number) {
    const token = process.env.GITHUB_TOKEN;
    const repo = process.env.GITHUB_WORKFLOW_REPO || 'bibhu2020/jobsearch';
    const branch = process.env.GITHUB_BRANCH || 'main';
    const headers: Record<string, string> = {
      Accept: 'application/vnd.github.v3+json',
      ...(token ? { Authorization: `token ${token}` } : {}),
    };

    const dirPath = `search_results/${userId}`;
    let entries: any[];
    try {
      const { data } = await axios.get(
        `https://api.github.com/repos/${repo}/contents/${dirPath}?ref=${branch}`,
        { headers },
      );
      entries = Array.isArray(data) ? data : [];
    } catch (err: any) {
      if (err?.response?.status === 404) return { imported: 0 };
      throw err;
    }

    let imported = 0;
    for (const entry of entries) {
      if (entry.type !== 'file' || !entry.name.endsWith('.json')) continue;
      try {
        const { data: fileData } = await axios.get(entry.url, { headers });
        const raw = Buffer.from(fileData.content.replace(/\s/g, ''), 'base64').toString('utf-8');
        const jobs: any[] = JSON.parse(raw);

        for (const job of jobs) {
          if (!job.url) continue;
          const exists = await this.db.get(
            'SELECT id FROM job_suggestions WHERE user_id = ? AND url = ?',
            [userId, job.url],
          );
          if (!exists) {
            await this.db.insert(
              `INSERT INTO job_suggestions
                 (user_id, title, company, location, description, url, match_reason, source,
                  search_date, match_score, matching, gaps, recommendation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
              [
                userId, job.title, job.company, job.location, job.description,
                job.url, job.match_reason, job.source, job.search_date,
                job.match_score ?? 0,
                JSON.stringify(job.matching ?? []),
                JSON.stringify(job.gaps ?? []),
                job.recommendation ?? 'consider',
              ],
            );
            imported++;
          }
        }
      } catch {
        // skip malformed files; don't abort the whole import
      }
    }

    return { imported };
  }

  async triggerSearch(userId: number, keywords?: string, country?: string) {
    const profile = await this.db.get<any>('SELECT * FROM user_profiles WHERE user_id = ?', [userId]);
    if (!profile?.profile_summary && !keywords?.trim()) {
      return { error: 'No profile analyzed yet. Enter keywords to search anyway.' };
    }

    const { data } = await axios.post(`${this.agentsUrl}/search/jobs`, {
      userId,
      profileSummary: profile?.profile_summary || '',
      skills:         profile?.skills     ? JSON.parse(profile.skills)     : [],
      experience:     profile?.experience ? JSON.parse(profile.experience) : [],
      keywords:       keywords?.trim() || '',
      location:       profile?.location || '',
      country:        country?.trim() || '',
    });

    let imported = 0;
    for (const job of data.jobs || []) {
      const exists = await this.db.get(
        'SELECT id FROM job_suggestions WHERE user_id = ? AND url = ?',
        [userId, job.url],
      );
      if (!exists) {
        await this.db.insert(
          `INSERT INTO job_suggestions
             (user_id, title, company, location, description, url, match_reason, source, search_date,
              match_score, matching, gaps, recommendation)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE, ?, ?, ?, ?)`,
          [
            userId, job.title, job.company, job.location, job.description, job.url,
            job.match_reason, job.source,
            job.match_score ?? 0,
            JSON.stringify(job.matching ?? []),
            JSON.stringify(job.gaps ?? []),
            job.recommendation ?? 'consider',
          ],
        );
        imported++;
      }
    }

    return { imported, suggestions: await this.getSuggestions(userId) };
  }

  async addToWishlist(userId: number, suggestionId: number) {
    const suggestion = await this.db.get<any>(
      'SELECT * FROM job_suggestions WHERE id = ? AND user_id = ?',
      [suggestionId, userId],
    );
    if (!suggestion) return { error: 'Suggestion not found' };

    const jobId = await this.db.insert(
      `INSERT INTO jobs (user_id, title, company, location, description, url, source)
       VALUES (?, ?, ?, ?, ?, ?, 'search_agent')`,
      [userId, suggestion.title, suggestion.company, suggestion.location,
       suggestion.description, suggestion.url],
    );
    const cardId = await this.db.insert(
      'INSERT INTO pipeline_cards (job_id, user_id, stage, position) VALUES (?, ?, ?, ?)',
      [jobId, userId, 'wishlist', 0],
    );

    await this.db.run(
      "UPDATE job_suggestions SET status = 'added' WHERE id = ? AND user_id = ?",
      [suggestionId, userId],
    );

    return { cardId, jobId };
  }

  async dismiss(userId: number, suggestionId: number) {
    await this.db.run(
      "UPDATE job_suggestions SET status = 'dismissed' WHERE id = ? AND user_id = ?",
      [suggestionId, userId],
    );
    return { dismissed: true };
  }

  async triggerGitHubAction(userId: number, keywords?: string, location?: string) {
    const token = process.env.GITHUB_TOKEN;
    if (!token) return { error: 'GITHUB_TOKEN not configured' };

    const profile = await this.db.get<any>('SELECT * FROM user_profiles WHERE user_id = ?', [userId]);
    if (!profile?.profile_summary && !keywords?.trim()) {
      return { error: 'No profile analyzed yet. Enter keywords to search anyway.' };
    }

    let skills: string[] = [];
    let experienceSlim: { title: string; company: string }[] = [];
    try {
      skills = profile?.skills ? JSON.parse(profile.skills) : [];
    } catch { skills = []; }
    try {
      const exp: any[] = profile?.experience ? JSON.parse(profile.experience) : [];
      experienceSlim = exp.slice(0, 3).map((e: any) => ({ title: e.title || '', company: e.company || '' }));
    } catch { experienceSlim = []; }

    const repo = process.env.GITHUB_WORKFLOW_REPO || 'bibhu2020/jobsearch';
    const workflow = process.env.GITHUB_WORKFLOW_FILE || 'job-search.yml';
    const ref = process.env.GITHUB_BRANCH || 'main';

    const inputs = {
      user_id:         String(userId),
      profile_summary: (profile?.profile_summary || '').slice(0, 2000),
      skills:          JSON.stringify(skills.slice(0, 15)),
      experience:      JSON.stringify(experienceSlim),
      keywords:        keywords?.trim() || '',
      location:        location?.trim() || profile?.location || '',
    };

    try {
      await axios.post(
        `https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`,
        { ref, inputs },
        { headers: { Authorization: `token ${token}`, Accept: 'application/vnd.github.v3+json' } },
      );
      return { dispatched: true };
    } catch (err: any) {
      const status = err?.response?.status;
      const message = err?.response?.data?.message || err.message;
      console.error(`GitHub Actions dispatch failed [${status}]: ${message}`);
      return { error: `GitHub API error ${status}: ${message}` };
    }
  }

  async getLatestWorkflowRun() {
    const token = process.env.GITHUB_TOKEN;
    if (!token) return null;

    const repo = process.env.GITHUB_WORKFLOW_REPO || 'bibhu2020/jobsearch';
    const workflow = process.env.GITHUB_WORKFLOW_FILE || 'job-search.yml';
    const headers = { Authorization: `token ${token}`, Accept: 'application/vnd.github.v3+json' };

    try {
      const { data: runsData } = await axios.get(
        `https://api.github.com/repos/${repo}/actions/workflows/${workflow}/runs?per_page=1&event=workflow_dispatch`,
        { headers },
      );
      const run = runsData.workflow_runs?.[0];
      if (!run) return null;

      const { data: jobsData } = await axios.get(
        `https://api.github.com/repos/${repo}/actions/runs/${run.id}/jobs`,
        { headers },
      );
      const steps: any[] = jobsData.jobs?.[0]?.steps || [];

      return {
        runId:      run.id,
        status:     run.status as string,     // queued | in_progress | completed
        conclusion: run.conclusion as string | null, // success | failure | cancelled | null
        createdAt:  run.created_at as string,
        runUrl:     run.html_url as string,
        steps: steps.map((s: any) => ({
          name:       s.name as string,
          status:     s.status as string,
          conclusion: s.conclusion as string | null,
        })),
      };
    } catch {
      return null;
    }
  }
}
