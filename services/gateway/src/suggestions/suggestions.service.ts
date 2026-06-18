import { Injectable } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import axios from 'axios';
import { readdirSync, readFileSync, existsSync } from 'fs';
import { join } from 'path';

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
    const dir = process.env.SEARCH_RESULTS_PATH || './search_results';
    if (!existsSync(dir)) return { imported: 0 };

    const files = readdirSync(dir).filter(f => f.endsWith('.json'));
    let imported = 0;

    for (const file of files) {
      const results: any[] = JSON.parse(readFileSync(join(dir, file), 'utf-8'));
      for (const job of results) {
        if (job.user_id && job.user_id !== userId) continue;
        const exists = await this.db.get(
          'SELECT id FROM job_suggestions WHERE user_id = ? AND url = ?',
          [userId, job.url],
        );
        if (!exists) {
          await this.db.insert(
            `INSERT INTO job_suggestions
               (user_id, title, company, location, description, url, match_reason, source, search_date)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [userId, job.title, job.company, job.location, job.description,
             job.url, job.match_reason, job.source, job.search_date],
          );
          imported++;
        }
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
      "UPDATE job_suggestions SET status = 'added' WHERE id = ?",
      [suggestionId],
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

  async triggerGitHubAction(keywords?: string, location?: string) {
    const token = process.env.GITHUB_TOKEN;
    if (!token) return { error: 'GITHUB_TOKEN not configured' };

    const repo = process.env.GITHUB_WORKFLOW_REPO || 'bibhu2020/jobsearch';
    const workflow = process.env.GITHUB_WORKFLOW_FILE || 'job-search.yml';
    const ref = process.env.GITHUB_BRANCH || 'main';

    try {
      await axios.post(
        `https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`,
        { ref, inputs: { keywords: keywords?.trim() || '', location: location?.trim() || '' } },
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
}
