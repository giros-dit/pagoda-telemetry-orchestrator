FROM node:latest

WORKDIR /app

COPY docker/ndac-http-dummy-server/app/* /app/

RUN npm install

CMD ["node", "app.js"]