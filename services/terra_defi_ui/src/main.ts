import Vue from 'vue';
import axios from 'axios';
import VueAxios from 'vue-axios';
import App from './App.vue';
import router from './router';
import Session from "@/utils/session";
import HttpService from "@/api/httpservice";

Vue.config.productionTip = false;


Vue.use(VueAxios, axios);
Vue.use(require('vue-moment'));

Session.init();
HttpService.init();

new Vue({
  router,
  render: (h) => h(App),
}).$mount('#app');
