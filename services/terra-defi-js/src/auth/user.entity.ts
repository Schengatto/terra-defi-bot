import { Column, Entity, OneToMany, PrimaryGeneratedColumn } from 'typeorm';
import { TaskDao } from '../tasks/task.entity';
import { User } from './user.model';
import { Exclude } from 'class-transformer';

@Entity()
export class UserDao implements User {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ unique: true })
    username: string;

    @Column()
    @Exclude({ toPlainOnly: true })
    password: string;

    @OneToMany((_type) => TaskDao, (task) => task.user, { eager: true })
    @Exclude({ toPlainOnly: true })
    tasks: TaskDao[];
}
