import { Injectable } from '@nestjs/common';
import axios from 'axios';
import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';

/**
 * Parses GITHUB_ARTIFACTS_PATH (e.g. https://github.com/bibhu2020/media/job_search_artifacts)
 * into { repo: 'bibhu2020/media', basePath: 'job_search_artifacts' }.
 */
function parseArtifactsPath(raw: string): { repo: string; basePath: string } {
  // Strip protocol + github.com
  const stripped = raw.replace(/^https?:\/\/github\.com\//, '').trim().replace(/\/$/, '');
  // stripped = "bibhu2020/media/job_search_artifacts"
  const parts = stripped.split('/');
  const repo = `${parts[0]}/${parts[1]}`;
  const basePath = parts.slice(2).join('/') || 'job_search_artifacts';
  return { repo, basePath };
}

@Injectable()
export class GitHubStorageService {
  private readonly token  = process.env.GITHUB_TOKEN;
  private readonly branch = process.env.GITHUB_BRANCH || 'main';
  private readonly repo: string;
  private readonly basePath: string;

  constructor() {
    const raw = process.env.GITHUB_ARTIFACTS_PATH || 'https://github.com/bibhu2020/media/job_search';
    const parsed = parseArtifactsPath(raw);
    this.repo     = parsed.repo;
    this.basePath = parsed.basePath;
  }

  private get apiBase() {
    return `https://api.github.com/repos/${this.repo}/contents/${this.basePath}`;
  }

  private get headers() {
    return {
      Authorization: `token ${this.token}`,
      Accept: 'application/vnd.github.v3+json',
    };
  }

  /**
   * Upload a buffer to GitHub. Returns the raw CDN URL.
   * Falls back to local disk when GITHUB_TOKEN is not set (local dev without token).
   */
  async upload(remotePath: string, content: Buffer, message: string): Promise<string> {
    if (!this.token) {
      const localPath = join(process.env.ARTIFACTS_PATH || './artifacts', remotePath);
      mkdirSync(dirname(localPath), { recursive: true });
      writeFileSync(localPath, content);
      return localPath;
    }

    const url = `${this.apiBase}/${remotePath}`;

    let sha: string | undefined;
    try {
      const { data } = await axios.get(url, { headers: this.headers });
      sha = data.sha;
    } catch { /* file does not exist yet — first upload */ }

    await axios.put(
      url,
      {
        message,
        content: content.toString('base64'),
        branch: this.branch,
        ...(sha ? { sha } : {}),
      },
      { headers: this.headers },
    );

    return `https://raw.githubusercontent.com/${this.repo}/${this.branch}/${this.basePath}/${remotePath}`;
  }
}
