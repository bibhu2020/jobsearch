import { Injectable, NotFoundException } from '@nestjs/common';
import { DatabaseService } from '../database/database.service';

const VALID_STAGES = ['wishlist', 'applied', 'interviewing', 'offer', 'rejected'];

@Injectable()
export class PipelineService {
  constructor(private db: DatabaseService) {}

  async getCards(userId: number) {
    return this.db.query(
      `SELECT pc.*, j.title, j.company, j.location, j.description, j.url, j.source
       FROM pipeline_cards pc
       JOIN jobs j ON pc.job_id = j.id
       WHERE pc.user_id = ?
       ORDER BY pc.stage, pc.position`,
      [userId],
    );
  }

  async moveCard(userId: number, cardId: number, stage: string, position: number) {
    if (!VALID_STAGES.includes(stage)) throw new NotFoundException('Invalid stage');
    const card = await this.db.get(
      'SELECT id FROM pipeline_cards WHERE id = ? AND user_id = ?',
      [cardId, userId],
    );
    if (!card) throw new NotFoundException('Card not found');
    await this.db.run(
      'UPDATE pipeline_cards SET stage = ?, position = ?, updated_at = NOW() WHERE id = ?',
      [stage, position, cardId],
    );
    return this.getCards(userId);
  }

  async updateNotes(userId: number, cardId: number, notes: string) {
    await this.db.run(
      'UPDATE pipeline_cards SET notes = ?, updated_at = NOW() WHERE id = ? AND user_id = ?',
      [notes, cardId, userId],
    );
    return { updated: true };
  }

  async deleteCard(userId: number, cardId: number) {
    const card = await this.db.get(
      'SELECT id FROM pipeline_cards WHERE id = ? AND user_id = ?',
      [cardId, userId],
    );
    if (!card) throw new NotFoundException('Card not found');
    await this.db.run('DELETE FROM pipeline_cards WHERE id = ?', [cardId]);
    return { deleted: true };
  }
}
