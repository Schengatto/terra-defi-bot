<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-light bg-red">
      <div class="navar-custom">
        <div class="navbar-brand" href="#">
          <span>Terra DeFi Bot</span></div>
      </div>
      <div>
        <button class="btb btn-sm btn-warning me-3 menu-button" type="button" aria-label="Toggle navigation" @click="toggleMenu">
          <span class="navbar-toggler-icon"></span>
        </button>
      </div>
    </nav>
    <div class="navbar-menu" v-if="isMenuVisible">
      <div class="row">
        <div class="col-sm-4">
          <a class="nav-link" href="#" @click="moveToWalletInfo()">Wallet Info</a>
          <a class="nav-link" href="#" @click="moveToMonitorEvents()">Events</a>
          <!--        <a class="nav-link" href="#" @click="moveToAssets()">Assets</a>-->
          <a class="nav-link" href="#" @click="moveToOpenOrders()">Orders</a>
          <a class="nav-link" href="#" @click="moveToPositions()">Positions</a>
          <a class="nav-link" href="#" @click="logout()">Logout</a>
        </div>
        <div class="col-sm-8">
          <ul class="list-group" v-if="coins.length">
            <li v-for="c in coins" :key="c.name"
                class="list-group-item d-flex justify-content-between align-items-center list-group-item-dark">
              <strong>{{ c.name }}</strong>
              <span class="badge bg-success rounded-pill">{{ c.amount.toFixed(2) }}</span>
            </li>
          </ul>
          <div v-else>
            <div class="spinner-border" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {Component, Vue} from "vue-property-decorator";
import {AuthUtils} from "@/utils/auth-utils";
import {AxiosResponse} from "axios";
import {BalanceCoin} from "@/models/bot.model";

const host = process.env.VUE_APP_API_SERVICE_HOST;
const port = process.env.VUE_APP_API_SERVICE_PORT;

@Component
export default class NavBar extends Vue {

  walletAddress: string = AuthUtils.username();
  coins: BalanceCoin[] = new Array<BalanceCoin>();
  isMenuVisible = false;

  public toggleMenu(): void {
    this.isMenuVisible = !this.isMenuVisible;
    if (this.isMenuVisible) {
      this.loadAccountBalance();
    }
  }

  private async loadAccountBalance(): Promise<void> {
    await this.$http
        .get(`${host}:${port}/wallet/balance-symbols`)
        .then((response: AxiosResponse) => {
          this.coins = Object.keys(response.data).map(coin => ({
            name: coin,
            amount: response.data[coin]
          })).filter(c => c.amount > 0);
        })
        .catch(error => {
          alert(`😖 ${error.response.data.message}`);
        });
  }

  public logout() {
    AuthUtils.removeAuthentication();
    this.$router.push({name: "login"});
  }

  public moveToOpenOrders() {
    this.$router.push({name: "openOrders"});
  }
  
  public moveToPositions() {
    this.$router.push({name: "positions"});
  }

  public moveToMonitorEvents() {
    this.$router.push({name: "monitors"});
  }

  public moveToAssets() {
    this.$router.push({name: "assets"});
  }

  public moveToWalletInfo() {
    this.$router.push({name: "walletInfo"});
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
.navbar {
  position: fixed;
  top: 0;
  width: 100%;
  z-index: 10;
}

.bg-red {
  background-color: #262627;
  color: #ffffff;
  border-bottom: 1px solid #1b1b2a;
}

.navbar {
  padding: 0 !important;
}

.navbar-brand {
  margin: 0;
  color: #ffffff !important;
  padding: 0.5em;
  background-color: #3e3c3c;
}

.nav-link {
  color: #ffffff !important;
  margin-top: 0.4em;
  font-weight: bold;

  &:hover {
    color: orangered !important;
  }
}

.nav-link:hover {
  color: yellow;
}

.btn-dark {
  font-variant: all-small-caps;
}

.navar-custom {
  display: grid;
  width: 100%;
  text-align: left;
  grid-template-columns: 16em auto 7em;
}

.menu-button {
  position: absolute;
  right: 1em;
  top: 0.5em;
}

.navbar-menu {
  position: fixed;
  top: 3em;
  right: 0;
  z-index: 10;
  background-color: #262627;
  width: 100%;
  max-width: 25em;
}

// Medium devices (tablets, 768px and up)
@media (max-width: 768px) {
}

#nav-links {
  display: flex;
}
</style>
