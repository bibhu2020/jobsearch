import { Module } from '@nestjs/common';
import { KitsController } from './kits.controller';
import { KitsService } from './kits.service';
import { AuthModule } from '../auth/auth.module';

@Module({
  imports: [AuthModule],
  controllers: [KitsController],
  providers: [KitsService],
})
export class KitsModule {}
