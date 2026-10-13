import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { createCipheriv, createDecipheriv, randomBytes } from 'crypto';

/**
 * AES-256-GCM encryption for user secrets (portal password, Gmail token, site sessions).
 * Key: CREDENTIALS_ENC_KEY = base64-encoded 32 bytes (`openssl rand -base64 32`).
 * Ciphertext format: v1:<iv b64>:<tag b64>:<data b64>
 */
@Injectable()
export class CryptoService {
  private readonly key: Buffer | null;

  constructor() {
    const raw = process.env.CREDENTIALS_ENC_KEY;
    const key = raw ? Buffer.from(raw, 'base64') : null;
    this.key = key && key.length === 32 ? key : null;
    if (raw && !this.key) {
      console.warn('CREDENTIALS_ENC_KEY must be base64 of exactly 32 bytes — secret storage disabled');
    }
  }

  isConfigured(): boolean {
    return this.key !== null;
  }

  private requireKey(): Buffer {
    if (!this.key) throw new ServiceUnavailableException('CREDENTIALS_ENC_KEY not configured');
    return this.key;
  }

  encrypt(plain: string): string {
    const iv = randomBytes(12);
    const cipher = createCipheriv('aes-256-gcm', this.requireKey(), iv);
    const data = Buffer.concat([cipher.update(plain, 'utf8'), cipher.final()]);
    const tag = cipher.getAuthTag();
    return ['v1', iv.toString('base64'), tag.toString('base64'), data.toString('base64')].join(':');
  }

  decrypt(payload: string): string {
    const [version, iv, tag, data] = payload.split(':');
    if (version !== 'v1' || !iv || !tag || !data) throw new Error('Unrecognized ciphertext format');
    const decipher = createDecipheriv('aes-256-gcm', this.requireKey(), Buffer.from(iv, 'base64'));
    decipher.setAuthTag(Buffer.from(tag, 'base64'));
    return Buffer.concat([decipher.update(Buffer.from(data, 'base64')), decipher.final()]).toString('utf8');
  }
}
