import { Module } from '@nestjs/common';
import { TasksModule } from './tasks/tasks.module';
import { WalletModule } from './wallet/wallet.module';
import { OrdersModule } from './orders/orders.module';
import { HealthModule } from './health/health.module';

@Module({
  imports: [TasksModule, WalletModule, OrdersModule, HealthModule],
  controllers: [],
  providers: [],
})
export class AppModule {}
