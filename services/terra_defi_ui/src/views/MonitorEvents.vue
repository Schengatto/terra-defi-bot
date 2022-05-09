<template>
  <div class="row">
    <div class="col table-responsive">
      <table class="table text-light">
        <thead>
        <tr>
          <th colspan="4" class="text-center bg-dark text-light">Monitor Events</th>
        </tr>
        <tr>
          <th>Token</th>
          <th>Event Type</th>
          <th>Message</th>
          <th>Date</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="event in events">
          <td> {{ event.symbol }}</td>
          <td> {{ event.type }}</td>
          <td> {{ event.message }}</td>
          <td> {{ event.updated }}</td>
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

interface MonitorEvent {
  id: string;
  lock_duration: number;
  message: string;
  name: string;
  symbol: string;
  type: string;
  updated: string;
}

@Component({
  name: "monitor-events"
})
export default class MonitorEvents extends Vue {
  public events: MonitorEvent[] = [];


  async mounted(): Promise<void> {
    await this.loadMonitorEvents();
  }

  private async loadMonitorEvents(): Promise<void> {
    await this.$http
        .get(`${host}:${port}/events`)
        .then((response: AxiosResponse) => this.events = response.data)
        .catch(error => {
          alert(`😖 ${error.response.data.message}`);
        });
  }
}
</script>

<style scoped lang="scss">
</style>
