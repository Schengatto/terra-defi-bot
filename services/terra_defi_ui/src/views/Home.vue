<template>
  <div id="home">
    <NavBar></NavBar>
    <div class="page-wrap">
      <router-view></router-view>
    </div>
  </div>
</template>

<script lang="ts">
import {Component, Vue} from "vue-property-decorator";
import NavBar from "@/components/layout/NavBar.vue";

@Component({
  components: {
    NavBar,
  },
})
export default class Home extends Vue {
}
</script>

<style lang="scss">
body {
  background-color: #1c1c1c;
}
.card-body {
  background-color: #343637;
  color: white;
}
caption {
  color: white;
}
#home {
  .page-wrap {
    margin-top: 5em;
    overflow: auto;
  }
}
</style>
