import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { NestExpressApplication } from '@nestjs/platform-express';
import { join } from 'path';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  app.setGlobalPrefix('api');

  // Serve compiled Vue frontend from dist/frontend/
  app.useStaticAssets(join(__dirname, 'frontend'), { index: false });

  // SPA fallback: any non-/api route returns index.html
  app.use((req: any, res: any, next: any) => {
    if (!req.path.startsWith('/api')) {
      res.sendFile(join(__dirname, 'frontend', 'index.html'));
    } else {
      next();
    }
  });

  app.enableCors({
    origin: process.env.NODE_ENV === 'production' ? true : (process.env.FRONTEND_URL || 'http://localhost:5173'),
    credentials: true,
  });
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));

  const port = parseInt(process.env.PORT || '3000', 10);
  await app.listen(port, '0.0.0.0');
  console.log(`Gateway running on http://0.0.0.0:${port}`);
}
bootstrap();
