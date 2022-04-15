import { Body, Controller, Delete, Get, Logger, Param, Patch, Post, Query, UseGuards } from '@nestjs/common';
import { TasksService } from './tasks.service';
import { Task } from './tasks.model';
import { CreateTaskDto } from './dto/create-task.dto';
import { GetTasksFilterDto } from './dto/get-tasks-filter.dto';
import { UpdateTaskStatusDto } from './dto/update-task.dto';
import { AuthGuard } from '@nestjs/passport';
import { User } from '../auth/user.model';
import { GetUser } from '../auth/get-user.decorator';

@Controller('tasks')
@UseGuards(AuthGuard())
export class TasksController {
    private logger = new Logger(TasksController.name);

    constructor(private tasksService: TasksService) {}

    @Get()
    async getTasks(@Query() filterDto: GetTasksFilterDto, @GetUser() user: User): Promise<Task[]> {
        this.logger.verbose(`User ${user.username} retrieving all tasks. Filters: ${JSON.stringify(filterDto)}`);
        return await this.tasksService.getTasks(filterDto, user);
    }

    @Get('/:id')
    async getTaskById(@Param('id') id, @GetUser() user: User): Promise<Task | null> {
        return await this.tasksService.getTaskById(id, user);
    }

    @Post()
    async createTask(@Body() createTaskDto: CreateTaskDto, @GetUser() user: User): Promise<Task> {
        return await this.tasksService.createTask(createTaskDto, user);
    }

    @Delete('/:id/')
    async deleteTask(@Param('id') id, @GetUser() user: User): Promise<void> {
        return await this.tasksService.deleteTask(id, user);
    }

    @Patch('/:id/status')
    async updateTask(@Param('id') id: string, @Body() updateTaskStatusDto: UpdateTaskStatusDto, @GetUser() user: User): Promise<Task | null> {
        const { status } = updateTaskStatusDto;
        return await this.tasksService.updateTask(id, status, user);
    }
}
