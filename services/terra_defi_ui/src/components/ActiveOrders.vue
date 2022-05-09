<template>
  <div class="card">
    <div class="card-header bg-dark text-white">
      <div class="row justify-content-between">
        <div class="col-sm-2">
          <div class="form-check form-switch">
            <input :disabled="!activeSymbol" class="form-check-input" type="checkbox" role="switch"
                   id="applySymbolFilter" v-model="applySymbolFilter">
            <label class="form-check-label" for="applySymbolFilter"><span v-if="activeSymbol">{{ activeSymbol }}</span>
              Orders</label>
          </div>
        </div>
        <div class="col txt-r">
          <button class="btn btn-sm btn-dancer" @click="onOrdersRefresh">🔄</button>
        </div>
      </div>
    </div>
    <div class="card-body">
      <div v-if="!symbolOrders.length">
        No active orders found
      </div>
      <div v-else class="card-content">
        <table class="table caption-top mb-4 text-light" v-for="go in symbolOrders">
          <caption><strong>{{ go.name }} @ {{go.price.toFixed(4)}}</strong></caption>
          <thead>
          <tr>
            <th class="txt-c">Type</th>
            <th class="txt-c">Token</th>
            <th class="txt-c">Price</th>
            <th class="txt-c">Amount</th>
            <th class="txt-c">Status</th>
            <th class="txt-c">Date</th>
            <th class="txt-c">Description</th>
            <th class="txt-c">Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="o in go.orders" :class="getOrderBg(o.type)">
            <td class=""> {{ o.type }}</td>
            <td> {{ o.token }}</td>
            <td class="txt-r"> {{ o.price.toFixed(2) }}</td>
            <td class="txt-r"> {{ o.amount.toFixed(2) }}</td>
            <td class="txt-c"><span :title="o.status">{{ getOrderStatusIcon(o.status) }}</span></td>
            <td> {{ o.updated }}</td>
            <td> {{ o.description }}</td>
            <td>
              <button class="btn btn-sm btn-dancer" @click="cancelOrder(o.id)">❌</button>
              <button class="btn btn-sm btn-dancer" @click="retryOrder(o.id)"
                      :disabled="isRetryOrderDisabled(o.status)">🔁
              </button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import {Component, Prop, Vue} from "vue-property-decorator";
import {ActiveOrderInfo, GetOrdersResponse, OrderStatus} from "@/models/bot.model";
import {orderAscByProperty} from "@/utils/array";

const host = process.env.VUE_APP_API_SERVICE_HOST;
const port = process.env.VUE_APP_API_SERVICE_PORT;

@Component({
  name: "active-orders"
})
export default class ActiveOrders extends Vue {
  @Prop({required: true})
  readonly ordersGroups!: GetOrdersResponse[];

  @Prop({required: true})
  readonly activeSymbol!: string;
  
  applySymbolFilter: boolean = true;

  getOrderStatusIcon(status: OrderStatus) {
    switch (status) {
      case OrderStatus.ToProcess:
        return "⏱️";
      case OrderStatus.Pending:
        return "⚙️";
      case OrderStatus.Processed:
        return "✔️️";
      case OrderStatus.Error:
        return "⚠️";
    }
  }

  cancelOrder(orderId: string): void {
    this.$emit("order:cancel", orderId)
  }

  retryOrder(orderId: string): void {
    this.$emit("order:retry", orderId)
  }

  isRetryOrderDisabled(status: OrderStatus): boolean {
    return [OrderStatus.ToProcess, OrderStatus.Processed].includes(status);
  }

  getOrderBg(orderType: string): string {
    switch (orderType) {
      case "BUY":
        return "bg-buy";
      case "SELL":
        return "bg-sell";
      case "WARN":
        return "bg-warn";
      default:
        return "bg-classic";
    }
  }

  onOrdersRefresh(): void {
    this.$emit("order:refresh");
  }

  get symbolOrders(): GetOrdersResponse[] {
    return this.ordersGroups
        .filter(go => this.applySymbolFilter ? go.name.includes(this.activeSymbol) : true)
        .map(go => ({...go, orders: orderAscByProperty(go.orders, "price")}))
        .map(go => ({...go, orders: go.orders.map(o => ({...o, amount: o.amount / 1000000}))}));
  }
}
</script>
<style lang="scss" scoped>
.card-content {
  max-height: 30em;
  overflow: auto;
}

.txt-r {
  text-align: right;
}

.txt-c {
  text-align: center;
}

.bg-buy {
  background-color: #2f4f4f;
}

.bg-sell {
  background-color: #523c97;
}

.bg-warn {
  background-color: #bb6b28;
}
</style>