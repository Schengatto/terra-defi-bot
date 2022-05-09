import {TOKEN_KEY, USERNAME_TOKEN_KEY} from '@/consts/app.constant';

export class AuthUtils {

    public static isAuthenticated(): boolean {
        return !!localStorage.getItem(TOKEN_KEY);
    }

    public static setAuthentication(token: string, username?: string): void {
        localStorage.setItem(TOKEN_KEY, this.encode(token));
        if (username) {
            localStorage.setItem(USERNAME_TOKEN_KEY,  this.encode(username));
        }
    }

    public static removeAuthentication(): void {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USERNAME_TOKEN_KEY);
    }

    public static authorizedHeader(): any {
        return this.isAuthenticated() 
            ? {authToken: this.decode(localStorage.getItem(TOKEN_KEY))} 
            : null;
    }

    public static username(): string {
        return this.isAuthenticated()
            ? this.decode(localStorage.getItem(USERNAME_TOKEN_KEY))
            : '';
    }
    
    private static encode(value: string | null): string {
        if (!value) return ""
        let hex, i;
        let result = "";
        for (i=0; i<value.length; i++) {
            hex = value.charCodeAt(i).toString(16);
            result += ("000"+hex).slice(-4);
        }
        return result
    }
    
    private static decode(value: string | null): string {
        if (!value) return ""
        let j;
        const hexes = value.match(/.{1,4}/g) || [];
        let back = "";
        for(j = 0; j<hexes.length; j++) {
            back += String.fromCharCode(parseInt(hexes[j], 16));
        }
        return back;
    }
}
