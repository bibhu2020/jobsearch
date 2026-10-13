import { Controller, Get, Post, Delete, Param, Query, Request, Res, UseGuards } from '@nestjs/common';
import { ApplyService } from '../apply/apply.service';
import { Response } from 'express';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { IntegrationsService } from './integrations.service';

@Controller('integrations')
export class IntegrationsController {
  constructor(private integrations: IntegrationsService, private apply: ApplyService) {}

  @Get('gmail/auth-url')
  @UseGuards(JwtAuthGuard)
  gmailAuthUrl(@Request() req) {
    return { url: this.integrations.gmailAuthUrl(req.user.userId, req.user.email) };
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

  /** Opens the live view on the site's sign-in page (LinkedIn, Dice). */
  @Post('sites/:site/connect')
  @UseGuards(JwtAuthGuard)
  connectSite(@Request() req, @Param('site') site: string) {
    return this.apply.startSiteLogin(req.user.userId, site);
  }

  @Delete('sites/:site')
  @UseGuards(JwtAuthGuard)
  disconnectSite(@Request() req, @Param('site') site: string) {
    return this.apply.disconnectSite(req.user.userId, site);
  }

  @Delete('gmail')
  @UseGuards(JwtAuthGuard)
  disconnectGmail(@Request() req) {
    return this.integrations.disconnectGmail(req.user.userId);
  }
}
