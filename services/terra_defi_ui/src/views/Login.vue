<template>
  <div id="page-wrapper">
    <div id="auth-container">
      <div class="mb-2 server-status">
        <small>
          service status
          <span v-if="isApiServiceUp">🟢</span>
          <span v-else>🔴</span>
        </small>
      </div>
      <div id="form-area" class="text-center">
        <form class="form-signin" @submit.prevent="handleSubmit()" autocomplete="off">
          <img class="mb-4 img-fluid"
               src="https://miro.medium.com/max/1400/1*PSjb_XLbhp10tPnGyefp2A.png"
               alt="terra-defi" height="60">
          <h2 class="h3 mb-3 font-weight-normal">Terra DeFi Bot</h2>
          <div class="row">
            <div class="col-lg-12">
              <label for="auth">API Token</label>
              <input id="auth" type="password" class="form-control" placeholder="API Token" v-model="form.authToken">
            </div>
            <div class="mt-3 d-grid gap-2 col-12 mx-auto">
              <button class="btn btn-primary btn-block"
                      :disabled="!form.authToken"
                      type="submit">ACCESS
              </button>
            </div>
          </div>
          <div class="alert alert-danger mt-2" role="alert" v-if="errorMessage">
            {{ errorMessage }}
          </div>
          <div class="mt-2">
            Created by Schengatto
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import {Component, Vue} from "vue-property-decorator";
import LoginForm from "@/models/login-form.model";
import {AxiosResponse} from "axios";
import {AuthUtils} from "@/utils/auth-utils";

const host = process.env.VUE_APP_API_SERVICE_HOST
const port = process.env.VUE_APP_API_SERVICE_PORT


const INIT_STATE: LoginForm = {username: "", password: ""};

@Component({
  components: {}
})
export default class Login extends Vue {
  public isApiServiceUp: boolean = false;
  public errorMessage= "";
  public form = {
    authToken: ""
  }
  private interval: any;

  public async mounted(): Promise<void> {
    this.checkServiceStatus();
    this.interval = setInterval(() => this.checkServiceStatus(), 60*1000)
  }

  destroy(): void {
    clearInterval(this.interval);
  }

  public async handleSubmit(): Promise<void> {
    await this.$http
        .post(`${host}:${port}/login`, {authToken: this.form.authToken})
        .then((response: AxiosResponse) => {
          AuthUtils.setAuthentication(this.form.authToken, response.data.walletAddress)
          this.$router.push({name: "walletInfo"});
        })
        .catch(e => {
          this.errorMessage = e;
        });
  }

  private async checkServiceStatus(): Promise<void> {
    const host = process.env.VUE_APP_API_SERVICE_HOST
    const port = process.env.VUE_APP_API_SERVICE_PORT
    await this.$http
        .get(`${host}:${port}/health`)
        .then((response: AxiosResponse) => this.isApiServiceUp = true)
        .catch(e => this.isApiServiceUp = false);
  }
}
</script>

<style scoped lang="scss">
.form-signin {
  width: 100%;
}

#page-wrapper {
  height: 100vh;
  overflow: hidden;
  background-color: #000000;
}

#auth-container {
  max-width: 30em;
  margin: 12% auto;
}

#form-area {
  background-color: snow;
  border-radius: 1em;
  border: 1px solid gold;
  color: #117a8b;
  padding: 3em 3em 3em 3em;
}

.btn-login {
  color: #573d03;
  background-color: #dec971;
  border: 1px solid #e5d05a;
  border-radius: 0 !important;
  font-variant: all-small-caps;
}

.server-status {
  color: white;
}

// Small devices (Mobile)
@media (max-width: 576px) {
  #page-wrapper {
    height: 100vh;
    overflow: hidden;
    background-color: snow;
  }

  #form-area {
    background-color: snow;
    border-radius: 0;
    border: 0px;
  }

  .server-status {
    color: black;
    text-align: center;
  }
}
</style>
