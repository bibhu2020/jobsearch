import { Controller, Get, Put, Delete, Body, Param, Request, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PipelineService } from './pipeline.service';

@Controller('pipeline')
@UseGuards(JwtAuthGuard)
export class PipelineController {
  constructor(private pipelineService: PipelineService) {}

  @Get('cards')
  getCards(@Request() req) {
    return this.pipelineService.getCards(req.user.userId);
  }

  @Put('cards/:id/move')
  moveCard(
    @Request() req,
    @Param('id') id: string,
    @Body() body: { stage: string; position: number },
  ) {
    return this.pipelineService.moveCard(req.user.userId, parseInt(id), body.stage, body.position);
  }

  @Put('cards/:id/notes')
  updateNotes(@Request() req, @Param('id') id: string, @Body() body: { notes: string }) {
    return this.pipelineService.updateNotes(req.user.userId, parseInt(id), body.notes);
  }

  @Delete('cards/:id')
  deleteCard(@Request() req, @Param('id') id: string) {
    return this.pipelineService.deleteCard(req.user.userId, parseInt(id));
  }
}
