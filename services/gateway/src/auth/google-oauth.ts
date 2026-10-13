import axios from 'axios';

/** Shared Google OAuth helpers (app sign-in and the Gmail connection use the same OAuth client). */
export const googleClientId = () => process.env.GOOGLE_OAUTH_CLIENT_ID;
export const googleClientSecret = () => process.env.GOOGLE_OAUTH_CLIENT_SECRET;
export const googleConfigured = () => !!(googleClientId() && googleClientSecret());

/** Where the browser goes after an OAuth round-trip ('' = same origin in production). */
export function frontendBase(): string {
  if (process.env.NODE_ENV === 'production') return '';
  return process.env.FRONTEND_URL || 'http://localhost:5173';
}

export function googleAuthUrl(params: Record<string, string>): string {
  return `https://accounts.google.com/o/oauth2/v2/auth?${new URLSearchParams({
    client_id: googleClientId()!,
    response_type: 'code',
    ...params,
  })}`;
}

export async function exchangeCode(code: string, redirectUri: string): Promise<any> {
  const { data } = await axios.post(
    'https://oauth2.googleapis.com/token',
    new URLSearchParams({
      code,
      client_id: googleClientId()!,
      client_secret: googleClientSecret()!,
      redirect_uri: redirectUri,
      grant_type: 'authorization_code',
    }),
  );
  return data;
}

export interface GoogleIdentity { sub: string; email: string; emailVerified: boolean; name: string | null }

/**
 * Reads the id_token returned by Google's token endpoint. It arrives directly from Google over TLS
 * in exchange for our client secret, so its signature does not need re-verifying; we still check
 * issuer, audience and expiry.
 */
export function readIdToken(idToken: string): GoogleIdentity {
  const payload = JSON.parse(Buffer.from(idToken.split('.')[1], 'base64url').toString('utf8'));
  const issuerOk = ['accounts.google.com', 'https://accounts.google.com'].includes(payload.iss);
  if (!issuerOk || payload.aud !== googleClientId() || payload.exp * 1000 < Date.now()) {
    throw new Error('Invalid Google ID token');
  }
  return {
    sub: String(payload.sub),
    email: String(payload.email || '').toLowerCase(),
    emailVerified: payload.email_verified === true || payload.email_verified === 'true',
    name: payload.name ?? null,
  };
}
