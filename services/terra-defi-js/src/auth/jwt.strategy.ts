import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { InjectRepository } from '@nestjs/typeorm';
import { UserDao } from './user.entity';
import { Repository } from 'typeorm';
import { JwtPayload } from './dto/jwt.dto';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
    constructor(@InjectRepository(UserDao) private userRepository: Repository<UserDao>, private configService: ConfigService) {
        super({ secretOrKey: configService.get('JWT_SECRET'), jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken() });
    }

    async validate(payload: JwtPayload): Promise<UserDao> {
        const { username } = payload;
        const user: UserDao = await this.userRepository.findOneBy({ username });
        if (!user) {
            throw new UnauthorizedException();
        }
        return user;
    }
}
