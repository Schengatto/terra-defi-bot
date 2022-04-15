import { createParamDecorator, ExecutionContext } from '@nestjs/common';
import { User } from './user.model';

export const GetUser = createParamDecorator((data, context: ExecutionContext): User => {
    const req = context.switchToHttp().getRequest();
    return req.user;
});
