import { Module } from '@nestjs/common';
import { ApplyController } from './apply.controller';
import { ApplyService } from './apply.service';
import { ApplySettingsService } from './apply-settings.service';
import { AuthModule } from '../auth/auth.module';

@Module({
  imports: [AuthModule],
  controllers: [ApplyController],
  providers: [ApplyService, ApplySettingsService],
  exports: [ApplySettingsService],
})
export class ApplyModule {}
