<template>
  <div class="container">
    <div class="container-body">
      <table class="table table-striped">
        <thead>
        <tr>
          <th colspan="3" class="text-center">Terra Pairs</th>
        </tr>
        <tr>
          <th>Symbol</th>
          <th>Contract</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="p in pairs">
          <td> {{ p.name }}</td>
          <td> {{ p.mainnet_contract }}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts">
import {Component, Vue} from "vue-property-decorator";
import {AxiosResponse} from "axios";
import NavBar from "@/components/NavBar.vue";

const host = process.env.VUE_APP_API_SERVICE_HOST
const port = process.env.VUE_APP_API_SERVICE_PORT

@Component({
  name: "assets"
})
export default class Assets extends Vue {
  public pairs = [];


  async mounted(): Promise<void> {
    await this.loadTerraPairs();
  }

  private async loadTerraPairs(): Promise<void> {
    await this.$http
        .get(`${host}:${port}/tokens-pairs`)
        .then((response: AxiosResponse) => this.pairs = response.data)
        .catch(error => {
          alert(`😖 ${error.response.data.message}`);
        });
  }
}
</script>

<style scoped lang="scss">
</style>
