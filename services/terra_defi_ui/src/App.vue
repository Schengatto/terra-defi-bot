<template>
  <div id="app">
    <router-view />
    <footer class="footer-site">
      <coingecko-coin-price-marquee-widget  coin-ids="bitcoin,anchor-protocol,mirror-protocol,astroport,terra-luna,terra-world-token,lunaverse,mars-protocol"
                                            currency="usd"
                                            background-color="#262627"
                                            locale="en"
                                            font-color="#ffffff">
      </coingecko-coin-price-marquee-widget>
    </footer>
  </div>
</template>

<style lang="scss">
#app {
  font-family: "Avenir", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #262627;
}
#nav {
  padding: 30px;
  a {
    font-weight: bold;
    color: #2c3e50;
    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
.footer-site{
  position: fixed;
  z-index: 10;
  bottom: 0;
}
</style>
