FROM node:16-alpine As development

ARG STAGE=prod
ENV STAGE=${STAGE}

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm cache clean --force && rm -rf node_modules && npm install

COPY . .

EXPOSE 5020:5020

CMD ["npm", "run", "start:prod"]
