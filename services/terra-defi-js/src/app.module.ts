import { Module } from '@nestjs/common';
import { TasksModule } from './tasks/tasks.module';
import { WalletModule } from './wallet/wallet.module';
import { OrdersModule } from './orders/orders.module';
import { HealthModule } from './health/health.module';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AuthModule } from './auth/auth.module';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { configValidationSchema } from './config.schema';
import { ThrottlerModule } from '@nestjs/throttler';

@Module({
    imports: [
        ConfigModule.forRoot({
            envFilePath: [`.env.stage.${process.env.STAGE || 'dev'}`],
            validationSchema: configValidationSchema
        }),
        TypeOrmModule.forRootAsync({
            imports: [ConfigModule],
            inject: [ConfigService],
            useFactory: async (configService: ConfigService) =>
                Object.assign({
                    type: configService.get('DB_TYPE') || 'postgres',
                    host: configService.get('DB_HOST') || 'localhost',
                    port: configService.get('DB_PORT') || 5432,
                    username: configService.get('DB_USERNAME') || 'postgres',
                    password: configService.get('DB_PASSWORD') || 'changeme',
                    database: configService.get('DB_NAME') || 'task-management',
                    autoLoadEntities: configService.get('DB_AUTO_LOAD_ENTITIES') || true,
                    synchronize: configService.get('DB_SYNC') || true
                })
        }),
        ThrottlerModule.forRoot({
            ttl: 1,
            limit: 1
        }),
        TasksModule,
        WalletModule,
        OrdersModule,
        HealthModule,
        AuthModule
    ],
    controllers: [],
    providers: []
})
export class AppModule {}
