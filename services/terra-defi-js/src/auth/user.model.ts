import { Task } from '../tasks/tasks.model';

export interface User {
    id: string;
    username: string;
    password: string;
    tasks: Task[];
}
