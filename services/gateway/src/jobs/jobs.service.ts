import { Injectable, NotFoundException } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import axios from 'axios';
import * as cheerio from 'cheerio';

@Injectable()
export class JobsService {
  private agentsUrl = process.env.AGENTS_URL || 'http://localhost:8000';

  constructor(private db: DatabaseService) {}

  async listJobs(userId: number) {
    return this.db.query('SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC', [userId]);
  }

  async addJob(userId: number, input: { url?: string; text?: string }) {
    let rawContent = input.text || '';
    let source = 'manual_text';

    if (input.url) {
      source = 'manual_url';
      try {
        const { data: html } = await axios.get(input.url, {
          timeout: 10000,
          headers: { 'User-Agent': 'Mozilla/5.0 (compatible; LinearLantern/1.0)' },
        });
        const $ = cheerio.load(html);
        $('script, style, nav, footer, header').remove();
        rawContent = $('body').text().replace(/\s+/g, ' ').trim().slice(0, 8000);
      } catch {
        rawContent = input.url;
      }
    }

    const { data: extracted } = await axios.post(`${this.agentsUrl}/jobs/extract`, {
      content: rawContent,
      url: input.url || null,
    });

    const jobId = await this.db.insert(
      `INSERT INTO jobs (user_id, title, company, location, description, url, source, raw_content)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        userId,
        extracted.title || 'Untitled Position',
        extracted.company || 'Unknown Company',
        extracted.location || '',
        extracted.description || rawContent,
        input.url || null,
        source,
        rawContent,
      ],
    );

    const cardId = await this.db.insert(
      'INSERT INTO pipeline_cards (job_id, user_id, stage, position) VALUES (?, ?, ?, ?)',
      [jobId, userId, 'wishlist', 0],
    );

    return {
      job: await this.db.get('SELECT * FROM jobs WHERE id = ?', [jobId]),
      cardId,
    };
  }

  async deleteJob(userId: number, jobId: number) {
    const job = await this.db.get('SELECT id FROM jobs WHERE id = ? AND user_id = ?', [jobId, userId]);
    if (!job) throw new NotFoundException('Job not found');
    await this.db.run('DELETE FROM jobs WHERE id = ? AND user_id = ?', [jobId, userId]);
    return { deleted: true };
  }
}
