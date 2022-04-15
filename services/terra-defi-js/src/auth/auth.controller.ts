import { Body, Controller, Post, Req, UseGuards } from '@nestjs/common';
import { AuthCredentialsDto } from './dto/auth-credentials.dto';
import { AuthService } from './auth.service';
import { JwtToken } from './dto/jwt.dto';
import { AuthGuard } from '@nestjs/passport';

@Controller('auth')
export class AuthController {
    constructor(private authService: AuthService) {}

    @Post('/signup')
    async signUp(@Body() authCredentialsDto: AuthCredentialsDto): Promise<void> {
        await this.authService.signUp(authCredentialsDto);
    }

    @Post('/signin')
    async singIn(@Body() authCredentialsDto: AuthCredentialsDto): Promise<JwtToken> {
        return await this.authService.signIn(authCredentialsDto);
    }

    @Post('/whoiam')
    @UseGuards(AuthGuard())
    async userDetails(@Req() req) {
        return { username: req.user.username };
    }
}
