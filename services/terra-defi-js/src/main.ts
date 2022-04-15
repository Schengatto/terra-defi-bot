import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { Logger, ValidationPipe } from '@nestjs/common';
import { TransformInterceptor } from './transform.interceptor';

async function bootstrap() {
    const logger = new Logger();
    logger.log('STAGE: ' + process.env.STAGE);
    const app = await NestFactory.create(AppModule);
    app.enableCors();
    app.useGlobalPipes(new ValidationPipe());
    app.useGlobalInterceptors(new TransformInterceptor());
    const port = 5020;
    await app.listen(port, '0.0.0.0');
    logger.log(`Application listening on port ${port}`);
}

bootstrap();
