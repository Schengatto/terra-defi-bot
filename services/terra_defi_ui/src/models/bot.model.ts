export enum OrderStatus {
    ToProcess = "TO_PROCESS",
    Pending = "PENDING",
    Processed = "PROCESSED",
    Error = "ERROR"
}

export interface WalletBalanceInfo {
    uluna?: number;
    uusd?: number;
}

export interface BalanceCoin {
    name: string;
    amount: number
}

export interface WalletTransaction {
    amount_offered: number;
    amount_received: number;
    asked_token: string;
    id: string;
    offered_token: string;
    pair: string;
    price: number;
    tx_hash: string;
    updated: string;
}

export interface GetOrdersResponse {
    name: string;
    orders: ActiveOrderInfo[];
    "terra_pair": string;
    price: number;
}

export interface ActiveOrderInfo {
    "amount": number;
    "id": string;
    "name": string;
    "price": number;
    "status": OrderStatus;
    "terra_pair":  string;
    "token": string;
    "type": string;
    "updated": string;
    "description"?: string;
}