<template>
  <div class="m-2">
    <create-order class="mb-4"
                  @symbol:change="setCurrentSymbol"
                  :message="message"
                  @order:create="onOrderCreated">
    </create-order>
    <active-orders class="mb-4"
                   :ordersGroups="ordersGroup"
                   :active-symbol="currentSymbol"
                   @order:refresh="loadOrders"
                   @order:cancel="onOrderCancel"
                   @order:retry="onOrderRetry"></active-orders>
  </div>
</template>

<script lang="ts">
import {Component, Vue} from "vue-property-decorator";
import ActiveOrders from "@/components/ActiveOrders.vue";
import CreateOrder from "@/components/CreateOrder.vue";
import {AxiosResponse} from "axios";
import {ActiveOrderInfo, GetOrdersResponse} from "@/models/bot.model";
import {AuthUtils} from "@/utils/auth-utils";
import Httpservice from "@/api/httpservice";

const host = process.env.VUE_APP_API_SERVICE_HOST;
const port = process.env.VUE_APP_API_SERVICE_PORT;

@Component({
  components: {CreateOrder, ActiveOrders}
})
export default class Orders extends Vue {
  public currentSymbol = "";
  public ordersGroup: GetOrdersResponse[] = new Array<GetOrdersResponse>();
  public message = "";
  private interval: any;


  async mounted(): Promise<void> {
    await this.loadOrders();
  }

  destroy(): void {
  }

  setCurrentSymbol(value: string): void {
    this.currentSymbol = value;
  }

  async onOrderCreated(form: any): Promise<void> {
    await this.createOrder(form);
    await this.loadOrders();
  }

  async onOrderCancel(orderId: string): Promise<void> {
    await this.cancelOrder(orderId);
    await this.loadOrders();
  }

  async onOrderRetry(orderId: string): Promise<void> {
    await this.retryOrder(orderId);
    await this.loadOrders();
  }

  private async createOrder(form: any): Promise<void> {
    await this.$http
        .post(`${host}:${port}/orders`, {
          "pair_name": form.pairName,
          "asked_token_symbol": form.token,
          "type": form.orderType,
          "price": form.price,
          "amount": form.amount * 1000000
        }, {headers: {...AuthUtils.authorizedHeader()}})
        .then((response: AxiosResponse) => {
          this.message = JSON.stringify(response.data);
        })
        .catch(error => {
          alert(`😖 ${error.message || JSON.stringify(error)}`);
        });
  }

  private async cancelOrder(orderId: string): Promise<void> {
    await this.$http
        .delete(`${host}:${port}/orders`, {
          params: {id: orderId},
          headers: {...AuthUtils.authorizedHeader()}
        })
        .then((response: AxiosResponse) => {
          this.message = JSON.stringify(response.data);
        })
        .catch(error => {
          alert(`😖 ${error.message || JSON.stringify(error)}`);
        });
  }

  private async retryOrder(orderId: string): Promise<void> {
    await this.$http
        .patch(`${host}:${port}/orders`,
            {},
            {
              params: {id: orderId},
              headers: {...AuthUtils.authorizedHeader()}
            })
        .then((response: AxiosResponse) => {
          this.message = JSON.stringify(response.data);
        })
        .catch(error => {
          alert(`😖 ${error.message || JSON.stringify(error)}`);
        });
  }

  public async loadOrders(): Promise<void> {
    const params = {"prices": true};
    await this.$http
        .get(`${host}:${port}/orders-grouped`, {params})
        .then((response: AxiosResponse) => {
          this.ordersGroup = response.data || []
        })
        .catch(error => {
          alert(`😖 ${error.message || JSON.stringify(error)}`);
        });
  }
}
</script>

<style scoped lang="scss">
</style>
