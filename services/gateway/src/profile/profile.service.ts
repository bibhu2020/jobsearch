import { Injectable } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import { GitHubStorageService } from '../github-storage/github-storage.service';
import axios from 'axios';
import pdfParse from 'pdf-parse';
import * as mammoth from 'mammoth';
import { extname } from 'path';

@Injectable()
export class ProfileService {
  private agentsUrl = process.env.AGENTS_URL || 'http://localhost:8000';

  constructor(
    private db: DatabaseService,
    private github: GitHubStorageService,
  ) {}

  async getProfile(userId: number) {
    const user = await this.db.get<any>('SELECT id, email, name, mode FROM users WHERE id = ?', [userId]);
    const profile = await this.db.get<any>('SELECT * FROM user_profiles WHERE user_id = ?', [userId]);
    return {
      ...user,
      profile: profile
        ? {
            ...profile,
            skills:     profile.skills     ? JSON.parse(profile.skills)     : [],
            experience: profile.experience ? JSON.parse(profile.experience) : [],
            education:  profile.education  ? JSON.parse(profile.education)  : [],
          }
        : null,
    };
  }

  async updateProfile(userId: number, data: {
    linkedinUrl?: string; name?: string; location?: string;
    profileSummary?: string; skills?: string[];
  }) {
    if (data.name) {
      await this.db.run('UPDATE users SET name = ? WHERE id = ?', [data.name, userId]);
    }
    await this.db.run(
      `UPDATE user_profiles SET
         linkedin_url    = COALESCE(?, linkedin_url),
         location        = COALESCE(?, location),
         profile_summary = COALESCE(?, profile_summary),
         skills          = COALESCE(?, skills),
         updated_at      = NOW()
       WHERE user_id = ?`,
      [
        data.linkedinUrl ?? null,
        data.location ?? null,
        data.profileSummary ?? null,
        data.skills !== undefined ? JSON.stringify(data.skills) : null,
        userId,
      ],
    );
    return this.getProfile(userId);
  }

  async saveResume(userId: number, buffer: Buffer, originalname: string) {
    const ext = extname(originalname).toLowerCase();

    // Extract raw text immediately so it's available for AI generation without re-reading the file
    let resumeText = '';
    try {
      if (ext === '.pdf') {
        resumeText = (await pdfParse(buffer)).text;
      } else if (['.doc', '.docx'].includes(ext)) {
        resumeText = (await mammoth.extractRawText({ buffer })).value;
      }
    } catch { /* unsupported format — continue without text */ }

    // Upload to GitHub (or local disk in dev)
    const remotePath = `resumes/${userId}/resume${ext}`;
    const resumeUrl = await this.github.upload(
      remotePath, buffer, `Resume upload for user ${userId}`,
    );

    await this.db.run(
      'UPDATE user_profiles SET resume_path = ?, resume_text = ?, updated_at = NOW() WHERE user_id = ?',
      [resumeUrl, resumeText, userId],
    );

    return { resumePath: resumeUrl };
  }

  async analyzeProfile(userId: number) {
    const profile = await this.db.get<any>('SELECT * FROM user_profiles WHERE user_id = ?', [userId]);
    if (!profile?.resume_text?.trim()) {
      throw new Error('No resume uploaded yet — please upload your resume first');
    }

    const { data } = await axios.post(`${this.agentsUrl}/profile/analyze`, {
      resumeText: profile.resume_text,
      linkedinUrl: profile.linkedin_url,
    });

    await this.db.run(
      `UPDATE user_profiles
       SET profile_summary = ?, skills = ?, experience = ?, education = ?, updated_at = NOW()
       WHERE user_id = ?`,
      [
        data.summary,
        JSON.stringify(data.skills || []),
        JSON.stringify(data.experience || []),
        JSON.stringify(data.education || []),
        userId,
      ],
    );

    return data;
  }
}
