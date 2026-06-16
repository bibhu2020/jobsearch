import { Controller, Get, Post, Put, Param, Body, Request, UseGuards, Res } from '@nestjs/common';
import { Response } from 'express';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { KitsService } from './kits.service';

@Controller('kits')
@UseGuards(JwtAuthGuard)
export class KitsController {
  constructor(private kitsService: KitsService) {}

  @Get('card/:cardId')
  getForCard(@Request() req, @Param('cardId') cardId: string) {
    return this.kitsService.getKitsForCard(req.user.userId, parseInt(cardId));
  }

  @Post('generate')
  generate(@Request() req, @Body() body: { cardId: number; type: string }) {
    return this.kitsService.generateKit(req.user.userId, body.cardId, body.type);
  }

  @Put(':id')
  update(@Request() req, @Param('id') id: string, @Body() body: { content: string }) {
    return this.kitsService.updateKit(req.user.userId, parseInt(id), body.content);
  }

  @Get(':id/download')
  async download(@Request() req, @Param('id') id: string, @Res() res: Response) {
    const { buffer, filename } = await this.kitsService.downloadKit(req.user.userId, parseInt(id));
    res.set({
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="${filename}"`,
    });
    res.send(buffer);
  }
}
