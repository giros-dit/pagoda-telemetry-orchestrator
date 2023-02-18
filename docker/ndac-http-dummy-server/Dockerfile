FROM node:latest

WORKDIR /app

COPY docker/ndac-http-dummy-server/app/* /app/

RUN npm install --package-lock-only

CMD ["node", "app.js"]
