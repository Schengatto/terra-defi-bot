<template>
  <div class="card m-2">
    <div class="card-header text-light bg-dark text-center"><strong>Wallet Info</strong></div>
    <div class="card-body">
      <div class="row">
        <div v-if="dataLoaded" class="col-12 table-responsive">
          <table class="table caption-top text-light">
            <caption>
              <div class="col-lg-2">
                <label for="symbol_selector">Transactions</label>
                <input id="symbol_selector" type="text" class="form-control" placeholder="filter"
                       v-model="txFilter">
              </div>
            </caption>
            <thead class="table-default">
            <tr>
              <th>Date</th>
              <th>From</th>
              <th>To</th>
              <th>Pair</th>
              <th>Amount</th>
              <th>Price</th>
              <th>Hash</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="t in transactions">
              <td>{{ t.updated }}</td>
              <td>{{ t.offered_token }}</td>
              <td>{{ t.asked_token }}</td>
              <td>{{ t.pair }}</td>
              <td>{{ t.amount_offered / 1000000 }}</td>
              <td>{{ t.price }}</td>
              <td><a class="hide-long-text" :href="'https://terrasco.pe/mainnet/tx/'+ t.tx_hash"
                     target="_blank">{{ t.tx_hash }}</a></td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import {AxiosResponse} from "axios";
import {BalanceCoin, WalletTransaction} from "@/models/bot.model";
import {AuthUtils} from "@/utils/auth-utils";

const host = process.env.VUE_APP_API_SERVICE_HOST;
const port = process.env.VUE_APP_API_SERVICE_PORT;

@Component({
  name: "wallet-info"
})
export default class WalletInfo extends Vue {

  walletAddress: string = AuthUtils.username();
  coins: BalanceCoin[] = new Array<BalanceCoin>();
  _transactions = new Array<WalletTransaction>();
  txFilter: string = "";
  dataLoaded: boolean = false;

  async beforeMount(): Promise<void> {
    await this.loadWalletTransactions();
    this.dataLoaded = true;
  }

  get transactions(): WalletTransaction[] {
    const filter = this.txFilter.toLowerCase();
    return this._transactions
        ? this._transactions.filter(t => t.pair.toLowerCase().includes(filter) || t.tx_hash.toLowerCase().includes(filter))
        : [];
  }

  private async loadWalletTransactions() {
    await this.$http
        .get(`${host}:${port}/wallet/transactions`)
        .then((response: AxiosResponse) => {
          this._transactions = response.data;
        })
        .catch(error => {
          alert(`😖 ${error.response.data.message}`);
        });
  }
}
</script>

<style scoped lang="css">
.hide-long-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>