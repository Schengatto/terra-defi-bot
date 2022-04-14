import { Module } from '@nestjs/common';
import { TasksController } from './tasks.controller';
import { TasksService } from './tasks.service';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TaskDao } from './task.entity';

@Module({
    imports: [TypeOrmModule.forFeature([TaskDao])],
    controllers: [TasksController],
    providers: [TasksService]
})
export class TasksModule {}
