import {Controller, Get} from '@nestjs/common';
import {HealthCheckResponse, ServiceStatus} from "./health.model";

@Controller('health')
export class HealthController {
    constructor() {
    }
    
    @Get("")
    async healthCheck(): Promise<HealthCheckResponse> {
        return {
            serviceStatus: ServiceStatus.Ok
        }
    }
    
}
