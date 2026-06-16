import { Injectable, NotFoundException } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import { GitHubStorageService } from '../github-storage/github-storage.service';
import axios from 'axios';

const KIT_TYPES = ['cover_letter', 'resume', 'interview_questions', 'company_brief'];

@Injectable()
export class KitsService {
  private agentsUrl = process.env.AGENTS_URL || 'http://localhost:8000';

  constructor(
    private db: DatabaseService,
    private github: GitHubStorageService,
  ) {}

  async getKitsForCard(userId: number, cardId: number) {
    const card = await this.db.get(
      'SELECT id FROM pipeline_cards WHERE id = ? AND user_id = ?',
      [cardId, userId],
    );
    if (!card) throw new NotFoundException('Card not found');
    return this.db.query('SELECT * FROM generated_kits WHERE pipeline_card_id = ?', [cardId]);
  }

  async generateKit(userId: number, cardId: number, type: string) {
    if (!KIT_TYPES.includes(type)) throw new NotFoundException('Invalid kit type');

    const card = await this.db.get<any>(
      `SELECT pc.*, j.title, j.company, j.location, j.description, j.url
       FROM pipeline_cards pc JOIN jobs j ON pc.job_id = j.id
       WHERE pc.id = ? AND pc.user_id = ?`,
      [cardId, userId],
    );
    if (!card) throw new NotFoundException('Card not found');

    const profile = await this.db.get<any>('SELECT * FROM user_profiles WHERE user_id = ?', [userId]);
    const userProfile = profile
      ? {
          summary:    profile.profile_summary,
          skills:     profile.skills     ? JSON.parse(profile.skills)     : [],
          experience: profile.experience ? JSON.parse(profile.experience) : [],
          education:  profile.education  ? JSON.parse(profile.education)  : [],
        }
      : {};

    const resumeText: string = profile?.resume_text || '';

    const { data } = await axios.post(
      `${this.agentsUrl}/generate/${type.replace(/_/g, '-')}`,
      { jobTitle: card.title, company: card.company, jobDescription: card.description, userProfile, resumeText },
    );

    const existing = await this.db.get<any>(
      'SELECT id FROM generated_kits WHERE pipeline_card_id = ? AND type = ?',
      [cardId, type],
    );

    if (existing) {
      await this.db.run(
        'UPDATE generated_kits SET content = ?, file_path = NULL, updated_at = NOW() WHERE id = ?',
        [data.content, existing.id],
      );
      return this.db.get('SELECT * FROM generated_kits WHERE id = ?', [existing.id]);
    } else {
      const kitId = await this.db.insert(
        'INSERT INTO generated_kits (pipeline_card_id, type, content) VALUES (?, ?, ?)',
        [cardId, type, data.content],
      );
      return this.db.get('SELECT * FROM generated_kits WHERE id = ?', [kitId]);
    }
  }

  async updateKit(userId: number, kitId: number, content: string) {
    const kit = await this.db.get<any>(
      `SELECT gk.* FROM generated_kits gk
       JOIN pipeline_cards pc ON gk.pipeline_card_id = pc.id
       WHERE gk.id = ? AND pc.user_id = ?`,
      [kitId, userId],
    );
    if (!kit) throw new NotFoundException('Kit not found');
    await this.db.run(
      'UPDATE generated_kits SET content = ?, file_path = NULL, updated_at = NOW() WHERE id = ?',
      [content, kitId],
    );
    return this.db.get('SELECT * FROM generated_kits WHERE id = ?', [kitId]);
  }

  async downloadKit(userId: number, kitId: number): Promise<{ buffer: Buffer; filename: string }> {
    const kit = await this.db.get<any>(
      `SELECT gk.*, pc.user_id, j.title, j.company
       FROM generated_kits gk
       JOIN pipeline_cards pc ON gk.pipeline_card_id = pc.id
       JOIN jobs j ON pc.job_id = j.id
       WHERE gk.id = ? AND pc.user_id = ?`,
      [kitId, userId],
    );
    if (!kit) throw new NotFoundException('Kit not found');

    const { data } = await axios.post(
      `${this.agentsUrl}/pdf/export`,
      { content: kit.content, type: kit.type, title: kit.title, company: kit.company },
      { responseType: 'arraybuffer' },
    );

    const buffer = Buffer.from(data);
    const filename = `${kit.type}.pdf`;

    // Upload to GitHub in background — don't block the download response
    const remotePath = `generated/${userId}/${kit.pipeline_card_id}/${filename}`;
    this.github.upload(remotePath, buffer, `Generated ${kit.type} PDF`).then((url) => {
      this.db.run('UPDATE generated_kits SET file_path = ? WHERE id = ?', [url, kitId]).catch(() => {});
    }).catch(() => {});

    return { buffer, filename };
  }
}
