import {
  Controller, Get, Post, Put, Delete,
  Param, Body, Request, UseGuards, UseInterceptors, UploadedFile,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';
import { extname } from 'path';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { InterviewerService } from './interviewer.service';

@Controller('interviewer')
@UseGuards(JwtAuthGuard)
export class InterviewerController {
  constructor(private svc: InterviewerService) {}

  // ── Mode ─────────────────────────────────────────────────────────────────────

  @Get('mode')
  getMode(@Request() req) {
    return this.svc.getMode(req.user.userId);
  }

  @Put('mode')
  setMode(@Request() req, @Body('mode') mode: string) {
    return this.svc.setMode(req.user.userId, mode);
  }

  // ── Projects ─────────────────────────────────────────────────────────────────

  @Get('projects')
  listProjects(@Request() req) {
    return this.svc.listProjects(req.user.userId);
  }

  @Post('projects')
  createProject(
    @Request() req,
    @Body('title') title: string,
    @Body('description') description?: string,
  ) {
    return this.svc.createProject(req.user.userId, title, description);
  }

  @Get('projects/:id')
  getProject(@Request() req, @Param('id') id: string) {
    return this.svc.getProject(req.user.userId, parseInt(id));
  }

  @Delete('projects/:id')
  deleteProject(@Request() req, @Param('id') id: string) {
    return this.svc.deleteProject(req.user.userId, parseInt(id));
  }

  // ── Candidates ────────────────────────────────────────────────────────────────

  @Post('projects/:pid/candidates')
  addCandidate(
    @Request() req,
    @Param('pid') pid: string,
    @Body('name') name: string,
    @Body('email') email?: string,
    @Body('resumeText') resumeText?: string,
  ) {
    return this.svc.addCandidate(req.user.userId, parseInt(pid), name, email, resumeText);
  }

  @Get('projects/:pid/candidates/:cid')
  getCandidate(@Request() req, @Param('pid') pid: string, @Param('cid') cid: string) {
    return this.svc.getCandidate(req.user.userId, parseInt(pid), parseInt(cid));
  }

  @Put('projects/:pid/candidates/:cid/notes')
  updateNotes(
    @Request() req,
    @Param('pid') pid: string,
    @Param('cid') cid: string,
    @Body('notes') notes: string,
  ) {
    return this.svc.updateCandidateNotes(req.user.userId, parseInt(pid), parseInt(cid), notes);
  }

  @Delete('projects/:pid/candidates/:cid')
  deleteCandidate(@Request() req, @Param('pid') pid: string, @Param('cid') cid: string) {
    return this.svc.deleteCandidate(req.user.userId, parseInt(pid), parseInt(cid));
  }

  @Post('projects/:pid/candidates/:cid/upload-resume')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: memoryStorage(),
      fileFilter: (_req, file, cb) => {
        const allowed = ['.pdf', '.doc', '.docx'];
        cb(null, allowed.includes(extname(file.originalname).toLowerCase()));
      },
      limits: { fileSize: 10 * 1024 * 1024 },
    }),
  )
  uploadResume(
    @Request() req,
    @Param('pid') pid: string,
    @Param('cid') cid: string,
    @UploadedFile() file: Express.Multer.File,
  ) {
    return this.svc.uploadResume(
      req.user.userId, parseInt(pid), parseInt(cid),
      file.buffer, file.originalname,
    );
  }

  @Post('projects/:pid/candidates/:cid/scan')
  scanResume(
    @Request() req,
    @Param('pid') pid: string,
    @Param('cid') cid: string,
    @Body('jobDescription') jobDescription?: string,
  ) {
    return this.svc.scanResume(req.user.userId, parseInt(pid), parseInt(cid), jobDescription);
  }

  // ── Pipeline cards ────────────────────────────────────────────────────────────

  @Put('cards/:cardId/move')
  moveCard(
    @Request() req,
    @Param('cardId') cardId: string,
    @Body('stage') stage: string,
    @Body('position') position: number,
  ) {
    return this.svc.moveCard(req.user.userId, parseInt(cardId), stage, position);
  }
}
