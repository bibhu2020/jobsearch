import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { Pool } from 'pg';

@Injectable()
export class DatabaseService implements OnModuleInit, OnModuleDestroy {
  private pool: Pool;

  onModuleInit() {
    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.DATABASE_URL?.includes('neon') || process.env.DATABASE_URL?.includes('sslmode')
        ? { rejectUnauthorized: false }
        : false,
      max: 10,
    });
  }

  async onModuleDestroy() {
    await this.pool?.end();
  }

  /** Auto-convert SQLite-style ? placeholders to PostgreSQL $1 $2 … */
  private pgify(sql: string): string {
    let i = 0;
    return sql.replace(/\?/g, () => `$${++i}`);
  }

  async query<T = any>(sql: string, params: any[] = []): Promise<T[]> {
    const result = await this.pool.query(this.pgify(sql), params);
    return result.rows as T[];
  }

  async get<T = any>(sql: string, params: any[] = []): Promise<T | undefined> {
    const result = await this.pool.query(this.pgify(sql), params);
    return result.rows[0] as T | undefined;
  }

  /** Run an UPDATE / DELETE — returns nothing. */
  async run(sql: string, params: any[] = []): Promise<void> {
    await this.pool.query(this.pgify(sql), params);
  }

  /** Run an INSERT and return the auto-generated id. */
  async insert(sql: string, params: any[] = []): Promise<number> {
    const text = this.pgify(sql.trimEnd().replace(/;$/, '')) + ' RETURNING id';
    const result = await this.pool.query(text, params);
    return result.rows[0].id as number;
  }
}
