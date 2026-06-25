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

  // ── Access control ───────────────────────────────────────────────────────────

  // Validates that userId is the owner or a member of projectId.
  // Returns the project owner's user_id so callers can use it for DB writes.
  private async getProjectOwnerId(userId: number, projectId: number): Promise<number> {
    const row = await this.db.get<any>(
      `SELECT p.user_id
       FROM interviewer_projects p
       WHERE p.id = ?
         AND (p.user_id = ? OR EXISTS (
           SELECT 1 FROM interviewer_project_members m
           WHERE m.project_id = p.id AND m.user_id = ?
         ))`,
      [projectId, userId, userId],
    );
    if (!row) throw new NotFoundException('Project not found or access denied');
    return row.user_id;
  }

  private async assertOwner(userId: number, projectId: number): Promise<void> {
    const p = await this.db.get(
      'SELECT id FROM interviewer_projects WHERE id = ? AND user_id = ?',
      [projectId, userId],
    );
    if (!p) throw new ForbiddenException('Only the project owner can perform this action');
  }

  // ── Projects ────────────────────────────────────────────────────────────────

  async listProjects(userId: number) {
    return this.db.query<any>(
      `SELECT p.id, p.title, p.description, p.created_at,
              (p.user_id = ?) AS is_owner,
              COUNT(DISTINCT c.id)::int AS candidate_count
       FROM interviewer_projects p
       LEFT JOIN interviewer_candidates c ON c.project_id = p.id
       WHERE p.user_id = ?
          OR EXISTS (
            SELECT 1 FROM interviewer_project_members m
            WHERE m.project_id = p.id AND m.user_id = ?
          )
       GROUP BY p.id
       ORDER BY p.created_at DESC`,
      [userId, userId, userId],
    );
  }

  async createProject(userId: number, title: string, description?: string) {
    const id = await this.db.insert(
      'INSERT INTO interviewer_projects (user_id, title, description) VALUES (?, ?, ?)',
      [userId, title, description || null],
    );
    const p = await this.db.get<any>('SELECT * FROM interviewer_projects WHERE id = ?', [id]);
    return { ...p, is_owner: true, candidate_count: 0 };
  }

  async getProject(userId: number, projectId: number) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);
    const project = await this.db.get<any>(
      'SELECT * FROM interviewer_projects WHERE id = ?',
      [projectId],
    );

    const cards = await this.db.query<any>(
      `SELECT ipc.id AS card_id, ipc.stage, ipc.position, ipc.created_at,
              ic.id, ic.project_id, ic.name, ic.email, ic.resume_path, ic.resume_text,
              ic.ai_summary, ic.ai_score, ic.ai_matching, ic.ai_gaps, ic.ai_recommendation, ic.notes
       FROM interviewer_pipeline_cards ipc
       JOIN interviewer_candidates ic ON ic.id = ipc.candidate_id
       WHERE ipc.project_id = ? AND ipc.user_id = ?
       ORDER BY ipc.stage, ipc.position`,
      [projectId, ownerId],
    );

    return {
      ...project,
      is_owner: project.user_id === userId,
      cards: cards.map((c: any) => ({
        ...c,
        ai_matching: c.ai_matching ? JSON.parse(c.ai_matching) : [],
        ai_gaps:     c.ai_gaps     ? JSON.parse(c.ai_gaps)     : [],
      })),
    };
  }

  async updateProject(userId: number, projectId: number, title: string, description?: string) {
    await this.assertOwner(userId, projectId);
    await this.db.run(
      'UPDATE interviewer_projects SET title = ?, description = ? WHERE id = ?',
      [title, description || null, projectId],
    );
    const p = await this.db.get<any>('SELECT * FROM interviewer_projects WHERE id = ?', [projectId]);
    return { ...p, is_owner: true };
  }

  async deleteProject(userId: number, projectId: number) {
    await this.assertOwner(userId, projectId);
    await this.db.run('DELETE FROM interviewer_projects WHERE id = ?', [projectId]);
    return { deleted: true };
  }

  // ── Members ──────────────────────────────────────────────────────────────────

  async listMembers(userId: number, projectId: number) {
    await this.getProjectOwnerId(userId, projectId); // validate access
    return this.db.query<any>(
      `SELECT u.id AS user_id, u.name, u.email, m.role, m.invited_at
       FROM interviewer_project_members m
       JOIN users u ON u.id = m.user_id
       WHERE m.project_id = ?
       ORDER BY m.invited_at ASC`,
      [projectId],
    );
  }

  async inviteMember(userId: number, projectId: number, email: string) {
    await this.assertOwner(userId, projectId);

    const invitee = await this.db.get<any>(
      'SELECT id, name, email FROM users WHERE email = ?',
      [email.toLowerCase().trim()],
    );
    if (!invitee) throw new NotFoundException('No account found with that email');
    if (invitee.id === userId) throw new ForbiddenException('You are already the project owner');

    await this.db.run(
      `INSERT INTO interviewer_project_members (project_id, user_id, role)
       VALUES (?, ?, 'editor')
       ON CONFLICT (project_id, user_id) DO NOTHING`,
      [projectId, invitee.id],
    );

    return this.listMembers(userId, projectId);
  }

  async removeMember(userId: number, projectId: number, memberId: number) {
    await this.assertOwner(userId, projectId);
    await this.db.run(
      'DELETE FROM interviewer_project_members WHERE project_id = ? AND user_id = ?',
      [projectId, memberId],
    );
    return this.listMembers(userId, projectId);
  }

  // ── Candidates ───────────────────────────────────────────────────────────────

  async addCandidate(
    userId: number,
    projectId: number,
    name: string,
    email?: string,
    resumeText?: string,
  ) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);

    const candidateId = await this.db.insert(
      `INSERT INTO interviewer_candidates (project_id, user_id, name, email, resume_text)
       VALUES (?, ?, ?, ?, ?)`,
      [projectId, ownerId, name, email || null, resumeText || null],
    );

    const position = await this.db.get<any>(
      `SELECT COUNT(*)::int AS cnt FROM interviewer_pipeline_cards
       WHERE project_id = ? AND stage = 'applied'`,
      [projectId],
    );
    await this.db.insert(
      `INSERT INTO interviewer_pipeline_cards (candidate_id, project_id, user_id, stage, position)
       VALUES (?, ?, ?, 'applied', ?)`,
      [candidateId, projectId, ownerId, position?.cnt ?? 0],
    );

    return this.getCandidate(userId, projectId, candidateId);
  }

  async getCandidate(userId: number, projectId: number, candidateId: number) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);
    const candidate = await this.db.get<any>(
      `SELECT ic.*, ipc.stage, ipc.position, ipc.id AS card_id
       FROM interviewer_candidates ic
       JOIN interviewer_pipeline_cards ipc ON ipc.candidate_id = ic.id
       WHERE ic.id = ? AND ic.project_id = ? AND ic.user_id = ?`,
      [candidateId, projectId, ownerId],
    );
    if (!candidate) throw new NotFoundException('Candidate not found');

    return {
      ...candidate,
      ai_matching: candidate.ai_matching ? JSON.parse(candidate.ai_matching) : [],
      ai_gaps:     candidate.ai_gaps     ? JSON.parse(candidate.ai_gaps)     : [],
    };
  }

  async updateCandidateNotes(userId: number, projectId: number, candidateId: number, notes: string) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);
    await this.db.run(
      `UPDATE interviewer_candidates SET notes = ?, updated_at = NOW()
       WHERE id = ? AND project_id = ? AND user_id = ?`,
      [notes, candidateId, projectId, ownerId],
    );
    return { updated: true };
  }

  async deleteCandidate(userId: number, projectId: number, candidateId: number) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);
    const c = await this.db.get(
      'SELECT id FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, ownerId],
    );
    if (!c) throw new NotFoundException('Candidate not found');
    await this.db.run(
      'DELETE FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, ownerId],
    );
    return { deleted: true };
  }

  async addCandidateFromResume(
    userId: number,
    projectId: number,
    stage: string,
    buffer: Buffer,
    originalname: string,
  ) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);
    const targetStage = VALID_STAGES.includes(stage) ? stage : 'applied';

    // Extract text from the uploaded file
    const ext = extname(originalname).toLowerCase();
    let resumeText = '';
    try {
      if (ext === '.pdf') {
        resumeText = (await pdfParse(buffer)).text;
      } else if (['.doc', '.docx'].includes(ext)) {
        resumeText = (await mammoth.extractRawText({ buffer })).value;
      }
    } catch { /* unreadable format — carry on with empty text */ }

    // Ask the AI agent to identify name + email from the resume
    let name = originalname.replace(/\.(pdf|docx?)$/i, '').replace(/[-_]/g, ' ').trim();
    let email: string | null = null;
    if (resumeText.trim()) {
      try {
        const { data: extracted } = await axios.post(
          `${this.agentsUrl}/interviewer/extract-candidate`,
          { resume_text: resumeText.slice(0, 3000) },
        );
        if (extracted.name) name = extracted.name;
        if (extracted.email) email = extracted.email;
      } catch { /* agent unreachable — fall back to filename */ }
    }

    // Upload file to GitHub storage using a timestamp path (candidateId not yet known)
    const remotePath = `interviewer/${ownerId}/projects/${projectId}/resumes/${Date.now()}${ext}`;
    const resumeUrl = await this.github.upload(remotePath, buffer, `Resume for ${name}`);

    // Create the candidate record
    const candidateId = await this.db.insert(
      `INSERT INTO interviewer_candidates (project_id, user_id, name, email, resume_path, resume_text)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [projectId, ownerId, name, email, resumeUrl, resumeText],
    );

    // Create the pipeline card in the target stage
    const pos = await this.db.get<any>(
      `SELECT COUNT(*)::int AS cnt FROM interviewer_pipeline_cards WHERE project_id = ? AND stage = ?`,
      [projectId, targetStage],
    );
    await this.db.insert(
      `INSERT INTO interviewer_pipeline_cards (candidate_id, project_id, user_id, stage, position)
       VALUES (?, ?, ?, ?, ?)`,
      [candidateId, projectId, ownerId, targetStage, pos?.cnt ?? 0],
    );

    return this.getCandidate(userId, projectId, candidateId);
  }

  async uploadResume(
    userId: number,
    projectId: number,
    candidateId: number,
    buffer: Buffer,
    originalname: string,
  ) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);
    const candidate = await this.db.get(
      'SELECT id FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, ownerId],
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

    const remotePath = `interviewer/${ownerId}/projects/${projectId}/candidates/${candidateId}/resume${ext}`;
    const resumeUrl = await this.github.upload(remotePath, buffer, `Resume for candidate ${candidateId}`);

    await this.db.run(
      `UPDATE interviewer_candidates SET resume_path = ?, resume_text = ?, updated_at = NOW()
       WHERE id = ? AND user_id = ?`,
      [resumeUrl, resumeText, candidateId, ownerId],
    );

    return { resumePath: resumeUrl, resumeText };
  }

  async scanResume(userId: number, projectId: number, candidateId: number, jobDescription?: string) {
    const ownerId = await this.getProjectOwnerId(userId, projectId);
    const candidate = await this.db.get<any>(
      'SELECT * FROM interviewer_candidates WHERE id = ? AND project_id = ? AND user_id = ?',
      [candidateId, projectId, ownerId],
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
        ownerId,
      ],
    );

    return data;
  }

  // ── Pipeline ─────────────────────────────────────────────────────────────────

  async moveCard(userId: number, cardId: number, stage: string, position: number) {
    if (!VALID_STAGES.includes(stage)) throw new NotFoundException('Invalid stage');

    const card = await this.db.get<any>(
      `SELECT ipc.id, ipc.project_id, p.user_id AS owner_id
       FROM interviewer_pipeline_cards ipc
       JOIN interviewer_projects p ON p.id = ipc.project_id
       WHERE ipc.id = ?
         AND (p.user_id = ? OR EXISTS (
           SELECT 1 FROM interviewer_project_members m
           WHERE m.project_id = ipc.project_id AND m.user_id = ?
         ))`,
      [cardId, userId, userId],
    );
    if (!card) throw new NotFoundException('Card not found or access denied');

    await this.db.run(
      `UPDATE interviewer_pipeline_cards SET stage = ?, position = ?, updated_at = NOW()
       WHERE id = ? AND user_id = ?`,
      [stage, position, cardId, card.owner_id],
    );
    return this.getProject(userId, card.project_id);
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
