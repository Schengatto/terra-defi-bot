import { User } from '../auth/user.model';

export interface Task {
    id: string;
    title: string;
    description: string;
    status: TaskStatus;
    user: User;
}

export enum TaskStatus {
    Open = 'OPEN',
    InProgress = 'IN_PROGRESS',
    Done = 'DONE'
}
