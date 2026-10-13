import { Controller, Get, Delete, Query, Request, Res, UseGuards } from '@nestjs/common';
import { Response } from 'express';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { IntegrationsService } from './integrations.service';

@Controller('integrations')
export class IntegrationsController {
  constructor(private integrations: IntegrationsService) {}

  @Get('gmail/auth-url')
  @UseGuards(JwtAuthGuard)
  gmailAuthUrl(@Request() req) {
    return { url: this.integrations.gmailAuthUrl(req.user.userId) };
  }

  /** Public: Google redirects here; the user is identified by the signed `state`. */
  @Get('gmail/callback')
  async gmailCallback(
    @Query('code') code: string,
    @Query('state') state: string,
    @Query('error') error: string,
    @Res() res: Response,
  ) {
    const ok = !error && (await this.integrations.gmailCallback(code, state));
    res.redirect(`${this.integrations.frontendBase()}/profile?gmail=${ok ? 'connected' : 'error'}`);
  }

  @Delete('gmail')
  @UseGuards(JwtAuthGuard)
  disconnectGmail(@Request() req) {
    return this.integrations.disconnectGmail(req.user.userId);
  }
}
