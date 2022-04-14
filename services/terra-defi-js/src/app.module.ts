import {Module} from '@nestjs/common';
import {TasksModule} from './tasks/tasks.module';
import {WalletModule} from './wallet/wallet.module';
import {OrdersModule} from './orders/orders.module';
import {HealthModule} from './health/health.module';
import {TypeOrmModule} from "@nestjs/typeorm";
import { AuthModule } from './auth/auth.module';

@Module({
    imports: [
        TypeOrmModule.forRoot({
            type: "postgres",
            host: "localhost",
            port: 5432,
            username: "postgres",
            password: "changeme",
            database: "task-management",
            autoLoadEntities: true,
            synchronize: true
        }),
        TasksModule,
        WalletModule,
        OrdersModule,
        HealthModule,
        AuthModule
    ],
    controllers: [],
    providers: [],
})
export class AppModule {
}
