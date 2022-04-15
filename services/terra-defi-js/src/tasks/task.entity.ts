import { Column, Entity, ManyToOne, PrimaryGeneratedColumn } from 'typeorm';
import { Task, TaskStatus } from './tasks.model';
import { UserDao } from '../auth/user.entity';
import { Exclude } from 'class-transformer';
import { User } from '../auth/user.model';

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

    @ManyToOne((_type) => UserDao, (user) => user.tasks, { eager: false })
    @Exclude({ toPlainOnly: true })
    user: UserDao;
}
