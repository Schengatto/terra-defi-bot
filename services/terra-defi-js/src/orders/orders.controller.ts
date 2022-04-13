import {Controller, Delete, Get, Patch, Post} from '@nestjs/common';
import {OrdersService} from "./orders.service";

@Controller('orders')
export class OrdersController {
    constructor(private ordersService: OrdersService) {
    }
    
    @Get("")
    async get(): Promise<any[]> {
        return await this.ordersService.getOrders()
    }

    @Post("")
    async create(): Promise<number> {
        return await this.ordersService.create({symbol: "LUNA"});
    }

    @Patch("")
    async update(): Promise<void> {
    }

    @Delete("")
    async remove(): Promise<void> {
    }
}
