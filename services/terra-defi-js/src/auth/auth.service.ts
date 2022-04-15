import { ConflictException, Injectable, InternalServerErrorException, UnauthorizedException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { UserDao } from './user.entity';
import { AuthCredentialsDto } from './dto/auth-credentials.dto';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { JwtToken } from './dto/jwt.dto';

@Injectable()
export class AuthService {
    constructor(@InjectRepository(UserDao) private userRepository: Repository<UserDao>, private jwtService: JwtService) {}

    async signUp(authCredentialsDto: AuthCredentialsDto): Promise<void> {
        const { username, password } = authCredentialsDto;
        const salt = await bcrypt.genSalt();
        const hashedPassword = await bcrypt.hash(password, salt);
        const user = await this.userRepository.create({ username, password: hashedPassword });
        try {
            await this.userRepository.save(user);
        } catch (error: any) {
            if (error.code === '23505') {
                throw new ConflictException('Username already exists');
            } else {
                throw new InternalServerErrorException();
            }
        }
    }

    async signIn(authCredentialsDto: AuthCredentialsDto): Promise<JwtToken> {
        const { username, password } = authCredentialsDto;
        const user = await this.userRepository.findOneBy({ username });
        if (user && (await bcrypt.compare(password, user.password))) {
            const accessToken = this.jwtService.sign({ username });
            return { accessToken };
        } else {
            throw new UnauthorizedException('Please check your login credentials');
        }
    }
}
