import { Module } from '@nestjs/common';
import { InterviewerController } from './interviewer.controller';
import { InterviewerService } from './interviewer.service';
import { AuthModule } from '../auth/auth.module';

@Module({
  imports: [AuthModule],
  controllers: [InterviewerController],
  providers: [InterviewerService],
})
export class InterviewerModule {}
