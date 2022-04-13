export enum ServiceStatus {
    Ok = "OK",
    KO = "KO"
}
export interface HealthCheckResponse {
    serviceStatus: ServiceStatus
}