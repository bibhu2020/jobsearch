import {
  Controller, Get, Put, Post, Body, Request, UseGuards,
  UseInterceptors, UploadedFile,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';
import { extname } from 'path';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { ProfileService } from './profile.service';

@Controller('profile')
@UseGuards(JwtAuthGuard)
export class ProfileController {
  constructor(private profileService: ProfileService) {}

  @Get()
  getProfile(@Request() req) {
    return this.profileService.getProfile(req.user.userId);
  }

  @Put()
  updateProfile(
    @Request() req,
    @Body() body: { name?: string; linkedinUrl?: string; location?: string; profileSummary?: string; skills?: string[] },
  ) {
    return this.profileService.updateProfile(req.user.userId, body);
  }

  @Post('resume')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: memoryStorage(),
      fileFilter: (req, file, cb) => {
        const allowed = ['.pdf', '.doc', '.docx'];
        cb(null, allowed.includes(extname(file.originalname).toLowerCase()));
      },
      limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
    }),
  )
  async uploadResume(@Request() req, @UploadedFile() file: Express.Multer.File) {
    return this.profileService.saveResume(req.user.userId, file.buffer, file.originalname);
  }

  @Post('analyze')
  async analyzeProfile(@Request() req) {
    return this.profileService.analyzeProfile(req.user.userId);
  }
}
