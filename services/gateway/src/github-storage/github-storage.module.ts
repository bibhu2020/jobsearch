import { Global, Module } from '@nestjs/common';
import { GitHubStorageService } from './github-storage.service';

@Global()
@Module({
  providers: [GitHubStorageService],
  exports: [GitHubStorageService],
})
export class GitHubStorageModule {}
