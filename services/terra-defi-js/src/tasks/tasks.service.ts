import { Injectable, NotFoundException } from '@nestjs/common';
import { Task, TaskStatus } from './tasks.model';
import { v4 as uuid } from 'uuid';
import { CreateTaskDto } from './dto/create-task.dto';
import { GetTasksFilterDto } from './dto/get-tasks-filter.dto';

@Injectable()
export class TasksService {
  private _tasks = new Array<Task>();

  async getAllTasks(): Promise<Task[]> {
    return this._tasks;
  }

  async getTasksWithFilter(filterDto: GetTasksFilterDto): Promise<Task[]> {
    const { status, search } = filterDto;
    let tasks = await this.getAllTasks();
    if (status) {
      tasks = tasks.filter((t) => t.status == status);
    }
    if (search) {
      return tasks.filter(
        (t) =>
          t.title.toLowerCase().includes(search.toLocaleLowerCase()) ||
          t.title.toLocaleLowerCase().includes(search.toLowerCase()),
      );
    }
    return tasks;
  }

  async getTaskById(id: string): Promise<Task> {
    const result = await this._tasks.find((t) => t.id == id);
    if (!result) {
      throw new NotFoundException(`Task with ID ${id}  not found`);
    }
    return result;
  }

  async createTask(createTaskDto: CreateTaskDto): Promise<Task> {
    const { title, description } = createTaskDto;
    const task: Task = {
      id: uuid(),
      title,
      description,
      status: TaskStatus.Open,
    };
    this._tasks.push(task);
    return task;
  }

  async deleteTask(id): Promise<void> {
    const task = await this.getTaskById(id);
    this._tasks = this._tasks.filter((t) => t.id !== task.id);
  }

  async updateTask(id: string, status: TaskStatus): Promise<Task> {
    const task = await this.getTaskById(id);
    if (task) {
      task.status = status;
    }
    return task;
  }
}
