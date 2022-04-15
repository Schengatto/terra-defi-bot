import { Injectable, InternalServerErrorException, Logger, NotFoundException } from '@nestjs/common';
import { Task, TaskStatus } from './tasks.model';
import { v4 as uuid } from 'uuid';
import { CreateTaskDto } from './dto/create-task.dto';
import { GetTasksFilterDto } from './dto/get-tasks-filter.dto';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { TaskDao } from './task.entity';
import { User } from '../auth/user.model';

@Injectable()
export class TasksService {
    private logger = new Logger(TasksService.name);

    constructor(
        @InjectRepository(TaskDao)
        private tasksRepository: Repository<TaskDao>
    ) {}

    private _tasks = new Array<Task>();

    async getTasks(filterDto: GetTasksFilterDto, user: User): Promise<Task[]> {
        const { status, search } = filterDto;
        const query = this.tasksRepository.createQueryBuilder('task');
        query.where({ user: user.id });

        if (status) {
            query.andWhere('task.status = :status', { status });
        }

        if (search) {
            query.andWhere('(LOWER(task.title) LIKE LOWER(:search) OR LOWER(task.description) LIKE LOWER(:search))', { search: `%${search}%` });
        }

        try {
            return await query.getMany();
        } catch (error) {
            this.logger.error(`Failed to get tasks for user "${user.username}. Filters: ${JSON.stringify(filterDto)}`, error);
            throw new InternalServerErrorException();
        }
    }

    async getTaskById(id: string, user: User): Promise<Task> {
        const result = await this.tasksRepository.findOneBy({ id, user });
        if (!result) {
            throw new NotFoundException(`Task with ID ${id}  not found`);
        }
        return result;
    }

    async createTask(createTaskDto: CreateTaskDto, user: User): Promise<Task> {
        const { title, description } = createTaskDto;
        const task: TaskDao = {
            id: uuid(),
            title,
            description,
            status: TaskStatus.Open,
            user: user
        };
        return await this.tasksRepository.save(task);
    }

    async deleteTask(id, user: User): Promise<void> {
        const result = await this.tasksRepository.delete({ id, user });
        if (!result.affected) {
            throw new NotFoundException(`Task with ID ${id}  not found`);
        }
    }

    async updateTask(id: string, status: TaskStatus, user: User): Promise<Task> {
        const task = await this.getTaskById(id, user);
        task.status = status;
        return await this.tasksRepository.save(task);
    }
}
