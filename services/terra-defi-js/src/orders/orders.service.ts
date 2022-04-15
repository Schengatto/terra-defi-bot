import { Injectable } from '@nestjs/common';

@Injectable()
export class OrdersService {
    async getOrders(): Promise<any[]> {
        return [];
    }

    async create(order: any): Promise<number> {
        return 1;
    }
}
