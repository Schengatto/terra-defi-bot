import { Injectable } from '@nestjs/common';

@Injectable()
export class TasksService {
    
    public doSomething(): string {
        return "test done"
    }
}
