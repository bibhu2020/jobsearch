import { Module } from '@nestjs/common';
import { IntegrationsController } from './integrations.controller';
import { IntegrationsService } from './integrations.service';
import { AuthModule } from '../auth/auth.module';
import { ApplyModule } from '../apply/apply.module';

@Module({
  imports: [AuthModule, ApplyModule],
  controllers: [IntegrationsController],
  providers: [IntegrationsService],
})
export class IntegrationsModule {}
