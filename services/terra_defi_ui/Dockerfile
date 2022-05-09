# build stage
FROM node:lts-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# production stage
FROM nginx:stable-alpine as production-stage

# CUSTOM NGINX CONF
COPY ./settings/nginx/*.* /etc/nginx/conf.d/

# SSL CERTS
COPY ./settings/certs/*.* /etc/ssl/certs/

COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80
EXPOSE 443

CMD ["nginx", "-g", "daemon off;"]