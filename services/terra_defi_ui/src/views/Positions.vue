<template>
  <div>
    <div class="card">
      <div class="card-header">
        <div class="row">
          <div class="col-11"><h5><b>Opened Positions</b></h5></div>
          <div v-if="isLoading" class="col-1 text-end">
            <div class="spinner-border spinner-border-sm" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
          <div v-else class="col-1 text-end">
            <button class="btn btn-sm btn-dancer" @click="getPositions()">🔄</button>
          </div>
        </div>
      </div>
      <div class="card-body bg-light table-responsive-sm">
        <table class="table text-end">
          <thead>
          <tr>
            <th colspan="2" class="text-center display-desktop">Token</th>
            <th class="display-desktop">Open Price</th>
            <th>Invested</th>
            <th>Amount</th>
            <th class="display-desktop">Current Price</th>
            <th>P/L ($)</th>
            <th>P/L (%)</th>
            <th class="display-desktop">Total</th>
            <th class="text-center">Actions</th>
          </tr>
          </thead>
          <tbody>
          <template v-for="p in positions">
            <tr class="display-mobile">
              <td colspan="7" class="text-start">
                <span class="me-4"><img :src="p.token_icon" height="20" :alt="p.token_symbol"></span>
                <span><b>{{ p.token_symbol }}</b></span>

              </td>
            </tr>
            <tr>
              <td class="display-desktop"><img :src="p.token_icon" height="20" :alt="p.token_symbol"></td>
              <td class="display-desktop"><b>{{ p.token_symbol }}</b></td>
              <td class="display-desktop"> {{ p.open_transaction_price.toFixed(2) }} $</td>
              <td> {{ getOfferedAmount(p) }} $</td>
              <td> {{ getTokenAmount(p) }}</td>
              <td class="display-desktop">
                <div><b>{{ getTokenCurrentPrice(p).toFixed(2) }} $</b></div>
              </td>
              <td>
                <div :class="getTextClass(getPositionProfit(p))"><b>{{ getPositionProfit(p).toFixed(2) }} $</b></div>
              </td>
              <td>
                <div :class="getTextClass(getPositionProfitPercentage(p))"><b>{{
                    getPositionProfitPercentage(p).toFixed(2)
                  }} %</b></div>
              </td>
              <td class="display-desktop"><b>{{ getPositionValue(p).toFixed(2) }} $</b></td>
              <td class="text-center">
                <div v-if="positionsInLoading.includes(p.id_position)">
                  <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                  </div>
                </div>
                <div v-else>
                  <button class="btn btn-sm btn-dancer" @click="closePosition(p)">❌</button>
                  <button class="btn btn-sm btn-dancer" @click="editPosition(p)">⚙️</button>
                </div>
              </td>
            </tr>
          </template>
          </tbody>
          <tfoot>
          <tr>
            <td colspan="2" class="display-desktop"></td>
            <td class="display-desktop"></td>
            <td class="text-end">{{ totalInvested.toFixed(2) }} $</td>
            <td></td>
            <td class="display-desktop" colspan="1"></td>
            <td class="text-end" :class="getTextClass(totalProfit)">{{ totalProfit.toFixed(2) }} $</td>
            <td class="text-end" :class="getTextClass(totalProfitPercentage)">{{ totalProfitPercentage.toFixed(2) }} %
            </td>
            <td class=" display-desktop text-end"><b>{{ totalCurrentPositions.toFixed(2) }} $</b></td>
            <td></td>
          </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {Component, Prop, Vue} from "vue-property-decorator";
import {ActiveOrderInfo, GetOrdersResponse, OrderStatus} from "@/models/bot.model";
import {orderAscByProperty} from "@/utils/array";
import {AuthUtils} from "@/utils/auth-utils";
import {AxiosResponse} from "axios";
import Httpservice from "@/api/httpservice";
import {Decimal} from "@/models/decimal";


interface Position {
  "close_transaction_amount_offered": number;
  "close_transaction_amount_received": number;
  "close_transaction_created": number | null;
  "close_transaction_hash": string | null;
  "close_transaction_price"?: number | null;
  "id_position": string;
  "open_transaction_amount_offered": number;
  "open_transaction_amount_received": number;
  "open_transaction_created": number;
  "open_transaction_hash": string;
  "open_transaction_price": number;
  "pair_mainnet_contract": string;
  "pair_name": string;
  "pair_testnet_contract": string;
  "stop_loss_price": number | null;
  "take_profit_price": number | null;
  "token_icon": string;
  "token_decimal_digits": number;
  "token_mainnet_contract": string;
  "token_symbol": string;
  "token_testnet_contract": string;
  "created": number;
  "updated": number;
  loading?: boolean;
}

@Component({
  name: "positions"
})
export default class Positions extends Vue {
  public positions: Position[] = [];
  public positionsInLoading: string[] = [];
  public message: string = "";
  public currentPrices: Record<string, number> = {};
  public isLoading: boolean = false;

  private interval: any = null;

  async mounted(): Promise<void> {
    await this.getPrices();
    await this.getPositions();
    this.interval = setInterval(() => this.getPrices(), 60 * 1000);
  }

  destroyed(): void {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }

  public getTokenAmount(position: Position): number {
    return (position.open_transaction_amount_received / 10 ** position.token_decimal_digits);
  }

  public getOfferedAmount(position: Position): number {
    return position.open_transaction_amount_offered / 10 ** position.token_decimal_digits;
  }

  public getTokenCurrentPrice(position: Position): number {
    return this.currentPrices[position.pair_mainnet_contract];
  }

  public getPositionProfit(position: Position): number {
    return this.getPositionValue(position) - this.getOfferedAmount(position);
  }

  public getPositionProfitPercentage(position: Position): number {
    const currentValue = this.getPositionValue(position);
    const initialValue = this.getOfferedAmount(position);
    return ((currentValue - initialValue) / initialValue) * 100;
  }

  public getPositionValue(position: Position): number {
    const currentPrice = this.getTokenCurrentPrice(position);
    return (this.getTokenAmount(position) * currentPrice);
  }

  public getTextClass(value: number): string {
    return value >= 0 ? "text-green" : "text-red";
  }

  get totalInvested(): number {
    return this.positions.reduce((acc, p) => acc + this.getOfferedAmount(p), 0);
  }

  get totalProfit(): number {
    return this.positions.reduce((acc, p) => acc + this.getPositionProfit(p), 0);
  }

  get totalProfitPercentage(): number {
    return ((this.totalCurrentPositions - this.totalInvested) / this.totalInvested) * 100;
  }

  get totalCurrentPositions(): number {
    return this.positions.reduce((acc, p) => acc + this.getPositionValue(p), 0);
  }

  public async closePosition(position: Position): Promise<void> {
    this.positionsInLoading.push(position.id_position);
    Httpservice.post<any>("/positions", {id: position.id_position})
        .then((response) => alert(`🟢 ${JSON.stringify(response)}`))
        .then(async () => await this.getPositions())
        .catch((error) => alert(`🔴 ${error}`))
        .finally(() => this.positionsInLoading = this.positionsInLoading.filter(p => p !== position.id_position));
  }

  public editPosition(position: Position): void {
    alert("🚧 Not implemented yet");
  }

  private async getPositions(): Promise<void> {
    this.isLoading = true;
    this.positions = await Httpservice.get<Position[]>("/positions", {include_closed: false});
    this.isLoading = false;
  }

  private async getPrices(): Promise<void> {
    this.currentPrices = await Httpservice.get<Record<string, number>>("/tokens/prices-ust");
  }
}
</script>

<style scoped>
.text-start {
  text-align: left;
}

.text-end {
  text-align: right;
}

.text-center {
  text-align: center;
}

.text-green {
  color: green;
}

.text-red {
  color: red;
}

@media (max-width: 768px) {
  .display-desktop {
    display: none;
  }
}

@media (min-width: 768px) {
  .display-mobile {
    display: none;
  }
}

</style>