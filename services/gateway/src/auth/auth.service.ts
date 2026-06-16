import { Injectable, ConflictException, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { DatabaseService } from '../database/database.service';

@Injectable()
export class AuthService {
  constructor(
    private db: DatabaseService,
    private jwt: JwtService,
  ) {}

  async register(name: string, email: string, password: string) {
    const existing = await this.db.get('SELECT id FROM users WHERE email = ?', [email]);
    if (existing) throw new ConflictException('Email already registered');

    const hash = await bcrypt.hash(password, 10);
    const userId = await this.db.insert(
      'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
      [name, email, hash],
    );
    await this.db.run('INSERT INTO user_profiles (user_id) VALUES (?)', [userId]);

    return this.issueToken(userId, email);
  }

  async login(email: string, password: string) {
    const user = await this.db.get<any>('SELECT * FROM users WHERE email = ?', [email]);
    if (!user) throw new UnauthorizedException('Invalid credentials');

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) throw new UnauthorizedException('Invalid credentials');

    return this.issueToken(user.id, user.email);
  }

  private issueToken(userId: number, email: string) {
    const token = this.jwt.sign({ sub: userId, email });
    return { token, user: { id: userId, email } };
  }
}
