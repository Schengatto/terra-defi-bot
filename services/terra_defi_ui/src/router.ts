import Vue from 'vue';
import Login from './views/Login.vue';
import VueRouter from 'vue-router';
import {AuthUtils} from "@/utils/auth-utils";
import {RawLocation, Route} from "vue-router/types/router";

Vue.use(VueRouter);

export default new VueRouter({
    routes: [
        {
            path: '/',
            name: 'login',
            component: Login,
        },
        {
            path: '/home',
            name: 'home',
            beforeEnter: (to, from, next) => {
                if (AuthUtils.isAuthenticated()) {
                    next();
                } else {
                    next({name: "login"});
                }
            },
            component: () => import(/* webpackChunkName: "home" */ './views/Home.vue'),
            // beforeEnter: (to, from, next) => {
                // return AuthUtils.isAuthenticated() ? next() : next('/');
            // },
            children:[
                {
                    path: '/wallet-info',
                    name: 'walletInfo',
                    component: () => import('./views/AccountInfo.vue'),
                },
                {
                    path: '/monitors',
                    name: 'monitors',
                    component: () => import('./views/MonitorEvents.vue'),
                },
                {
                    path: '/assets',
                    name: 'assets',
                    component: () => import('./views/Assets.vue'),
                },
                {
                    path: '/open-orders',
                    name: 'openOrders',
                    component: () => import('./views/Orders.vue'),
                },
                {
                    path: '/positions',
                    name: 'positions',
                    component: () => import('./views/Positions.vue'),
                },
            ]
        },
    ],
});
