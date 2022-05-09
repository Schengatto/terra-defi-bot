<template>
  <div class="card">
    <div class="card-header bg-dark text-white" @click="cardExpanded = !cardExpanded">
      Order Management <small>(1 UST = 1000000 uusd)</small>
    </div>
    <div class="card-body" v-if="cardExpanded">
      <div>
        <form @submit.prevent="submitOrder">
          <div class="row">
            <div class="col-lg-2">
              <label for="orderType">Order Type</label>
              <select class="form-select" id="orderType" v-model="form.orderType">
                <option v-for="order in orderTypes" :key="order.id" :value="order.id">{{ order.name }}</option>
              </select>
            </div>
            <div class="col-lg-2" v-if="form.orderType !== 'CANCEL'">
              <label for="symbol_selector">Token</label>
              <input id="symbol_selector"
                     type="text"
                     class="form-control"
                     placeholder="Symbol"
                     v-model="form.token">
            </div>
            <div class="col-lg-4" v-if="form.orderType !== 'CANCEL'" :key="form.token">
              <label for="pair_selector">Pair</label>
              <select class="form-control" id="pair_selector" v-model="form.pairName" @change="updateFilter">
                <option v-for="t in filteredPairs" :value="t.name" :key="t.name">{{ t.name }}</option>
              </select>
            </div>
            <div class="col-lg-2" v-if="form.orderType !== 'CANCEL'">
              <label for="amount">Offered amount</label>
              <input id="amount" type="number" class="form-control" placeholder="Quantity" v-model="form.amount"
                     min="0" autocomplete="off">
            </div>
            <div class="col-lg-2" v-if="form.orderType !== 'CANCEL'">
              <label for="price">Price</label>
              <input id="price" type="number" class="form-control" placeholder="Stop Loss" v-model="form.price"
                     min="0" autocomplete="off">
            </div>
            <div class="col-lg-6" v-if="form.orderType === 'CANCEL'">
              <label for="orderId">Order Id</label>
              <input id="orderId" type="text" class="form-control" placeholder="Order Id" v-model="form.orderId"
                     autocomplete="off">
            </div>
          </div>
          <div class="row mt-3 justify-content-between">
            <div class="col-lg-4">
              <div>
                <button type="button"
                        class="btn btn-warning me-2"
                        @click="clearForm">Clear
                </button>
                <button type="button"
                        class="btn btn-primary"
                        :disabled="!isFormValid"
                        @click="submitOrder">Execute
                </button>
              </div>
            </div>
            <div class="col-lg-8" v-if="swapPrice">
              <div class="alert alert-warning alert-sm p-1 mt-1">
                <span class="text-right">{{ swapPrice }}</span>
                <span class="refresh-icon" title="reload" @click="updateFilter" v-if="!loadingPrice">🔃</span>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
    <div class="card-footer" v-if="message">
      <div>
        <pre>{{ message }}</pre>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import {AxiosResponse} from "axios";
import {Prop, Watch} from "vue-property-decorator";
import {EnumDropdownItem} from "@/models/common.model";
import {getEnumDropdown} from "@/utils/enum";

const host = process.env.VUE_APP_API_SERVICE_HOST
const port = process.env.VUE_APP_API_SERVICE_PORT

enum OrderType {
  Buy = "BUY",
  Sell = "SELL",
  Warn = "WARN",
  Cancel = "CANCEL"
}

@Component({
  name: "create-order"
})
export default class CreateOrder extends Vue {
  @Prop({type: String, default: ""})
  public message = "";

  public orders: any[] = [];
  public pairs: any[] = [];
  public swapPrice = "";
  public reserveToken1: number = 0;
  public reserveToken2: number = 0;

  loadingPrice = false;
  cardExpanded = true;

  private interval?: number;

  public form = {
    orderType: OrderType.Warn,
    pairName: "",
    token: "",
    amount: 0,
    price: 0,
    orderId: "",
    authToken: ""
  }

  @Watch("form")
  async updateFilter(): Promise<void> {
    if (this.form.pairName) {
      this.loadingPrice = true
      const response = await this.$http
          .get(`${host}:${port}/tokens/pairs-price`, {params: {"pair_name": this.form.pairName}})
          .then((response: AxiosResponse) => response.data)
          .catch(error => {
            alert(`😖 ${error.response.data.message}`);
          });
      try {
        const [token1, token2] = response;
        this.reserveToken1 = token1.reserve / 1000000;
        this.reserveToken2 = token2.reserve / 1000000;
        this.swapPrice = `1 ${token1.symbol} = ${parseFloat(token1.price).toFixed(4)} ${token2.symbol} @ ${this.reserveToken1.toFixed(0)} | 1 ${token2.symbol} = ${parseFloat(token2.price).toFixed(4)} ${token1.symbol}  @ ${this.reserveToken2.toFixed(0)}`;
      } catch (e) {
        console.error(e);
        this.swapPrice = "";
      } finally {
        this.loadingPrice = false;
      }
    }
    this.$emit("symbol:change", this.form.pairName);
  }


  get filteredPairs(): any[] {
    return this.pairs.filter(p => p.name.includes(this.form.token))
  }

  async mounted(): Promise<void> {
    await this.loadTerraPairs()
  }

  private async loadTerraPairs(): Promise<void> {
    await this.$http
        .get(`${host}:${port}/tokens-pairs`, {params: {name:"UST"}})
        .then((response: AxiosResponse) => this.pairs = response.data)
        .catch(error => {
          alert(`😖 ${error.response.data.message}`);
        });
  }

  destroyed(): void {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }

  public clearForm(): void {
    this.form = {
      orderType: OrderType.Warn,
      pairName: "",
      token: "",
      amount: 0,
      price: 0,
      orderId: "",
      authToken: this.form.authToken
    }
  }

  public async submitOrder(): Promise<void> {
    if ([OrderType.Buy, OrderType.Sell, OrderType.Warn].includes(this.form.orderType)) {
      this.$emit("order:create", this.form);
    } else if ([OrderType.Cancel].includes(this.form.orderType)) {
      this.$emit("order:cancel", this.form.orderId);
    }

  }

  get isFormValid(): boolean {
    switch (this.form.orderType) {
      case OrderType.Buy:
        return this.form.pairName !== null && !!this.form.amount && this.form.price >= 0;
      case OrderType.Sell:
        return this.form.pairName !== null && !!this.form.amount;
      case OrderType.Cancel:
        return !!this.form.orderId;
      default:
        return this.form.pairName !== null;
    }
  }

  get orderTypes(): EnumDropdownItem[] {
    return getEnumDropdown(OrderType).filter(o => o.id !== OrderType.Cancel)
  }
}
</script>
<style lang="scss" scoped>
.refresh-icon {
  position: absolute;
  right: 1em;
  cursor: pointer;
}
</style>