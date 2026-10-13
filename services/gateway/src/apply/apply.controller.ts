import { Controller, Get, Put, Post, Param, Body, Request, Res, UseGuards } from '@nestjs/common';
import { Response } from 'express';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { ApplyService } from './apply.service';
import { ApplySettingsService } from './apply-settings.service';

@Controller('apply')
@UseGuards(JwtAuthGuard)
export class ApplyController {
  constructor(
    private applyService: ApplyService,
    private settingsService: ApplySettingsService,
  ) {}

  @Get('settings')
  getSettings(@Request() req) {
    return this.settingsService.getSettings(req.user.userId);
  }

  @Put('settings')
  updateSettings(
    @Request() req,
    @Body() body: { portalPassword?: string; autoSubmit?: boolean; easyApplyDailyCap?: number; defaults?: Record<string, any> },
  ) {
    return this.settingsService.updateSettings(req.user.userId, body);
  }

  @Post('cards/:cardId/start')
  start(@Request() req, @Param('cardId') cardId: string) {
    return this.applyService.start(req.user.userId, parseInt(cardId));
  }

  @Get('cards/:cardId/runs')
  cardRuns(@Request() req, @Param('cardId') cardId: string) {
    return this.applyService.getCardRuns(req.user.userId, parseInt(cardId));
  }

  @Get('runs/active')
  active(@Request() req) {
    return this.applyService.getActiveRun(req.user.userId);
  }

  @Get('runs/:runId')
  getRun(@Request() req, @Param('runId') runId: string) {
    return this.applyService.getRun(req.user.userId, runId);
  }

  @Get('runs/:runId/screenshot')
  async screenshot(@Request() req, @Param('runId') runId: string, @Res() res: Response) {
    const jpeg = await this.applyService.getScreenshot(req.user.userId, runId);
    res.set({ 'Content-Type': 'image/jpeg', 'Cache-Control': 'private, max-age=3600' });
    res.send(jpeg);
  }

  @Post('runs/:runId/input')
  input(@Request() req, @Param('runId') runId: string, @Body() body: any) {
    return this.applyService.input(req.user.userId, runId, body);
  }

  @Post('runs/:runId/verification')
  verification(@Request() req, @Param('runId') runId: string, @Body() body: { value: string }) {
    return this.applyService.provideVerification(req.user.userId, runId, body?.value);
  }

  @Post('runs/:runId/:action')
  control(@Request() req, @Param('runId') runId: string, @Param('action') action: string) {
    return this.applyService.control(req.user.userId, runId, action);
  }
}
