import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';
import { GitHubStorageService } from '../github-storage/github-storage.service';
import axios from 'axios';
import pdfParse from 'pdf-parse';
import * as mammoth from 'mammoth';
import { extname } from 'path';

const VALID_STAGES = ['applied', 'screening', 'interview', 'offer', 'rejected'];

@Injectable()
export class InterviewerService {
  private agentsUrl = process.env.AGENTS_URL || 'http://localhost:8000';

  constructor(
    private db: DatabaseService,
    private github: GitHubStorageService,
  ) {}

  // ── Projects ────────────────────────────────────────────────────────────────

  async listProjects(userId: number) {
    const projects = await this.db.query<any>(
      `SELECT p.*, COUNT(c.id)::int AS candidate_count
       FROM interviewer_projects p
       LEFT JOIN interviewer_candidates c ON c.project_id = p.id
       WHERE p.user_id = ?
       GROUP BY p.id
       ORDER BY p.created_at DESC`,
      [userId],
    );
    return projects;
  }

  async createProject(userId: number, title: string, description?: string) {
    const id = await this.db.insert(
      'INSERT INTO interviewer_projects (user_id, title, description) VALUES (?, ?, ?)',
      [userId, title, description || null],
    );
    return this.db.get('SELECT * FROM interviewer_projects WHERE id = ?', [id]);
  }

  async getProject(userId: number, projectId: number) {
    const project = await this.db.get<any>(
      'SELECT * FROM interviewer_projects WHERE id = ? AND user_id = ?',
      [projectId, userId],
    );
    if (!project) throw new NotFoundException('Project not found');

    const cards = await this.db.query<any>(
      `SELECT ipc.*, ic.name, ic.email, ic.ai_score, ic.ai_recommendation, ic.notes
       FROM interviewer_pipeline_cards ipc
       JOIN interviewer_candidates ic ON ic.id = ipc.candidate_id
       WHERE ipc.project_id = ? AND ipc.user_id = ?
       ORDER BY ipc.stage, ipc.position`,
      [projectId, userId],
    );

    return { ...project, cards };
  }

  async deleteProject(userId: number, projectId: number) {
    const p = await this.db.get(
      'SELECT id FROM interviewer_projects WHERE id = ? AND user_id = ?',
      [projectId, userId],
    );
    if (!p) throw new NotFoundException('Project not found');
    await this.db.run('DELETE FROM interviewer_projects WHERE id = ? AND user_id = ?', [projectId, userId]);
    return { deleted: true };
  }

  // ── Candidates ───────────────────────────────────────────────────────────────

  async addCandidate(
    userId: number,
    projectId: number,
    name: string,
    email?: string,
    resumeText?: string,
  ) {
    const project = await this.db.get(
      'SELECT id FROM interviewer_projects WHERE id = ? AND user_id = ?',
      [projectId, userId],
    );
    if (!project) throw new NotFoundException('Project not found');

    const candidateId = await this.db.insert(
      `INSERT INTO interviewer_candidates (project_id, user_id, name, email, resume_text)
       VALUES (?, ?, ?, ?, ?)`,
      [projectId, userId, name, email || null, resumeText || null],
    );

    const position = await this.db.get<any>(
      `SELECT COUNT(*)::int AS cnt FROM interviewer_pipeline_cards
       WHERE project_id = ? AND stage = 'applied'`,
      [projectId],
    );
    await this.db.insert(
      `INSERT INTO interviewer_pipeline_cards (candidate_id, project_id, user_id, stage, position)
       VALUES (?, ?, ?, 'applied', ?)`,
      [candidateId, projectId, userId, position?.cnt ?? 0],
    );

    return this.getCandidate(userId, projectId, candidateId);
  }

  async getCandidate(userId: number, projectId: number, candidateId: number) {
    const candidate = await this.db.get<any>(
      `SELECT ic.*, ipc.stage, ipc.position, ipc.id AS card_id
       FROM interviewer_candidates ic
       JOIN interviewer_pipeline_cards ipc ON ipc.candidate_id = ic.id
       WHERE ic.id = ? AND ic.project_id = ? AND ic.user_id = ?`,
      [candidateId, projectId, userId],
    );
    if (!candidate) throw new NotFoundException('Candidate not found');

    return {
      ...candidate,
      ai_matching: candidate.ai_matching ? JSON.parse(candidate.ai_matching) : [],
      ai_gaps:     candidate.ai_gaps     ? JSON.parse(candidate.ai_gaps)     : [],
    };
  }

  async updateCandidateNotes(userId: number, projectId: number, candidateId: number, notes: string) {
    await this.db.run(
      `UPDATE interviewer_candidates SET notes = ?, updated_at = NOW()
       WHERE id = ? AND project_id = ? AND user_id = ?`,
      [notes, candidateId, projectId, userId],
    );
    return { updated: true };
  }

  async deleteCandidate(userId: number, projectId: number, candidateId: number) {
    const c = await this.db.get(
      'SELECT id FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, userId],
    );
    if (!c) throw new NotFoundException('Candidate not found');
    await this.db.run(
      'DELETE FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, userId],
    );
    return { deleted: true };
  }

  async uploadResume(
    userId: number,
    projectId: number,
    candidateId: number,
    buffer: Buffer,
    originalname: string,
  ) {
    const candidate = await this.db.get(
      'SELECT id FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, userId],
    );
    if (!candidate) throw new NotFoundException('Candidate not found');

    const ext = extname(originalname).toLowerCase();
    let resumeText = '';
    try {
      if (ext === '.pdf') {
        resumeText = (await pdfParse(buffer)).text;
      } else if (['.doc', '.docx'].includes(ext)) {
        resumeText = (await mammoth.extractRawText({ buffer })).value;
      }
    } catch { /* unsupported format */ }

    const remotePath = `interviewer/${userId}/projects/${projectId}/candidates/${candidateId}/resume${ext}`;
    const resumeUrl = await this.github.upload(remotePath, buffer, `Resume for candidate ${candidateId}`);

    await this.db.run(
      `UPDATE interviewer_candidates SET resume_path = ?, resume_text = ?, updated_at = NOW()
       WHERE id = ? AND user_id = ?`,
      [resumeUrl, resumeText, candidateId, userId],
    );

    return { resumePath: resumeUrl, resumeText };
  }

  async scanResume(userId: number, projectId: number, candidateId: number, jobDescription?: string) {
    const candidate = await this.db.get<any>(
      'SELECT * FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, userId],
    );
    if (!candidate) throw new NotFoundException('Candidate not found');
    if (!candidate.resume_text?.trim()) {
      throw new ForbiddenException('No resume text available — upload a resume first');
    }

    const { data } = await axios.post(`${this.agentsUrl}/interviewer/scan-resume`, {
      resume_text: candidate.resume_text,
      job_description: jobDescription || '',
    });

    await this.db.run(
      `UPDATE interviewer_candidates
       SET ai_summary = ?, ai_score = ?, ai_matching = ?, ai_gaps = ?, ai_recommendation = ?,
           updated_at = NOW()
       WHERE id = ? AND user_id = ?`,
      [
        data.summary,
        data.score,
        JSON.stringify(data.matching || []),
        JSON.stringify(data.gaps || []),
        data.recommendation,
        candidateId,
        userId,
      ],
    );

    return data;
  }

  // ── Pipeline ─────────────────────────────────────────────────────────────────

  async moveCard(userId: number, cardId: number, stage: string, position: number) {
    if (!VALID_STAGES.includes(stage)) throw new NotFoundException('Invalid stage');
    const card = await this.db.get(
      'SELECT id, project_id FROM interviewer_pipeline_cards WHERE id = ? AND user_id = ?',
      [cardId, userId],
    );
    if (!card) throw new NotFoundException('Card not found');
    await this.db.run(
      `UPDATE interviewer_pipeline_cards SET stage = ?, position = ?, updated_at = NOW()
       WHERE id = ? AND user_id = ?`,
      [stage, position, cardId, userId],
    );
    return this.getProject(userId, (card as any).project_id);
  }

  // ── User mode ────────────────────────────────────────────────────────────────

  async getMode(userId: number): Promise<string> {
    const user = await this.db.get<any>('SELECT mode FROM users WHERE id = ?', [userId]);
    return user?.mode ?? 'candidate';
  }

  async setMode(userId: number, mode: string): Promise<{ mode: string }> {
    if (!['candidate', 'interviewer'].includes(mode)) {
      throw new ForbiddenException('Invalid mode');
    }
    await this.db.run('UPDATE users SET mode = ? WHERE id = ?', [mode, userId]);
    return { mode };
  }
}
