import { Controller, Get, Post, Delete, Body, Param, Request, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { JobsService } from './jobs.service';

@Controller('jobs')
@UseGuards(JwtAuthGuard)
export class JobsController {
  constructor(private jobsService: JobsService) {}

  @Get()
  list(@Request() req) {
    return this.jobsService.listJobs(req.user.userId);
  }

  @Post()
  add(@Request() req, @Body() body: { url?: string; text?: string }) {
    return this.jobsService.addJob(req.user.userId, body);
  }

  @Delete(':id')
  remove(@Request() req, @Param('id') id: string) {
    return this.jobsService.deleteJob(req.user.userId, parseInt(id));
  }
}
