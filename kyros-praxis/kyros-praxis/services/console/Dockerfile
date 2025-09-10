FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./

RUN npm install -g npm@latest

RUN npm config set registry https://registry.npmjs.org/

RUN npm cache clean --force

RUN npm install

COPY . .

RUN npm run build

FROM node:20-alpine as runtime

WORKDIR /app

COPY --from=builder /app/.next/standalone ./

COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]