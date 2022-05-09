<template>
  <wallet-info></wallet-info>
</template>

<script lang="ts">
import {Component, Vue} from "vue-property-decorator";
import WalletInfo from "@/components/WalletInfo.vue";

@Component({
  name: "home",
  components: {
    WalletInfo,
  },
})
export default class Home extends Vue {
}
</script>
