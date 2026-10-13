import { Controller, Get, Query, Req, Res } from '@nestjs/common';
import { Request, Response } from 'express';
import { randomBytes } from 'crypto';
import { AuthService } from './auth.service';
import { frontendBase } from './google-oauth';

const NONCE_COOKIE = 'll_oauth_nonce';

function readCookie(req: Request, name: string): string | undefined {
  const match = (req.headers.cookie || '').split(';').map(c => c.trim()).find(c => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : undefined;
}

@Controller('auth')
export class AuthController {
  constructor(private auth: AuthService) {}

  /** Starts Google sign-in (the browser navigates here). */
  @Get('google')
  google(@Res() res: Response) {
    let url: string;
    try {
      const nonce = randomBytes(16).toString('hex');
      url = this.auth.googleLoginUrl(nonce);
      res.cookie(NONCE_COOKIE, nonce, {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 10 * 60 * 1000,
        path: '/api/auth',
      });
    } catch (err: any) {
      return res.redirect(`${frontendBase()}/login?error=${encodeURIComponent(err.message)}`);
    }
    res.redirect(url);
  }

  @Get('google/callback')
  async googleCallback(
    @Query('code') code: string,
    @Query('state') state: string,
    @Query('error') error: string,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    res.clearCookie(NONCE_COOKIE, { path: '/api/auth' });
    if (error || !code || !state) {
      return res.redirect(`${frontendBase()}/login?error=${encodeURIComponent('Google sign-in was cancelled')}`);
    }
    try {
      const { token } = await this.auth.googleLogin(code, state, readCookie(req, NONCE_COOKIE));
      // Fragment, not query string: never sent to servers or written to access logs.
      res.redirect(`${frontendBase()}/auth/callback#token=${encodeURIComponent(token)}`);
    } catch (err: any) {
      // Axios errors from Google carry details in response.data; Nest exceptions in response.message.
      const google = err?.response?.data;
      const detail = google
        ? `Google ${err.response.status}: ${google.error ?? ''} ${google.error_description ?? ''}`.trim()
        : `${err?.constructor?.name ?? 'Error'}: ${err?.message ?? err}`;
      console.warn(`auth: Google sign-in failed — ${detail}`);
      const userMessage = err?.status === 401 && typeof err?.message === 'string' ? err.message : 'Google sign-in failed — please try again';
      res.redirect(`${frontendBase()}/login?error=${encodeURIComponent(userMessage)}`);
    }
  }
}
