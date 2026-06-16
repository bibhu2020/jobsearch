import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { DatabaseModule } from './database/database.module';
import { GitHubStorageModule } from './github-storage/github-storage.module';
import { AuthModule } from './auth/auth.module';
import { ProfileModule } from './profile/profile.module';
import { JobsModule } from './jobs/jobs.module';
import { PipelineModule } from './pipeline/pipeline.module';
import { KitsModule } from './kits/kits.module';
import { SuggestionsModule } from './suggestions/suggestions.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env'],   // resolved from process.cwd() = project root in both dev and Docker
      ignoreEnvFile: false,
    }),
    DatabaseModule,
    GitHubStorageModule,
    AuthModule,
    ProfileModule,
    JobsModule,
    PipelineModule,
    KitsModule,
    SuggestionsModule,
  ],
})
export class AppModule {}
