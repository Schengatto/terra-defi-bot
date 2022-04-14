import { Injectable, NotFoundException } from '@nestjs/common';
import { Task, TaskStatus } from './tasks.model';
import { v4 as uuid } from 'uuid';
import { CreateTaskDto } from './dto/create-task.dto';
import { GetTasksFilterDto } from './dto/get-tasks-filter.dto';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { TaskDao } from './task.entity';
import { filter } from 'rxjs';

@Injectable()
export class TasksService {
    constructor(
        @InjectRepository(TaskDao)
        private tasksRepository: Repository<TaskDao>
    ) {}

    private _tasks = new Array<Task>();

    async getTasks(filterDto: GetTasksFilterDto): Promise<Task[]> {
        const { status, search } = filterDto;
        const query = this.tasksRepository.createQueryBuilder('task');

        if (status) {
            query.andWhere('task.status = :status', { status });
        }

        if (search) {
            query.andWhere('LOWER(task.title) LIKE LOWER(:search) OR LOWER(task.description) LIKE LOWER(:search)', { search: `%${search}%` });
        }

        return await query.getMany();
    }

    async getTaskById(id: string): Promise<Task> {
        const result = await this.tasksRepository.findOneBy({ id });
        if (!result) {
            throw new NotFoundException(`Task with ID ${id}  not found`);
        }
        return result;
    }

    async createTask(createTaskDto: CreateTaskDto): Promise<Task> {
        const { title, description } = createTaskDto;
        const task: TaskDao = {
            id: uuid(),
            title,
            description,
            status: TaskStatus.Open
        };
        return await this.tasksRepository.save(task);
    }

    async deleteTask(id): Promise<void> {
        const result = await this.tasksRepository.delete({ id });
        if (!result.affected) {
            throw new NotFoundException(`Task with ID ${id}  not found`);
        }
    }

    async updateTask(id: string, status: TaskStatus): Promise<Task> {
        const task = await this.getTaskById(id);
        task.status = status;
        return await this.tasksRepository.save(task);
    }
}
