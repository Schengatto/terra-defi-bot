import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';
import { Task, TaskStatus } from './tasks.model';

@Entity()
export class TaskDao implements Task {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    title: string;

    @Column()
    description: string;

    @Column()
    status: TaskStatus;
}
