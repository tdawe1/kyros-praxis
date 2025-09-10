# syntax=docker/dockerfile:1
FROM node:20-alpine AS build
WORKDIR /app
# Install build deps for node-gyp; setuptools provides a distutils shim for Python 3.12+
RUN apk add --no-cache \
      python3 \
      py3-setuptools \
      make \
      g++ \
      linux-headers \
 && npm i -g npm@11 \
 && npm --version

# Copy daemon package files (only package.json to avoid stale/invalid lockfile)
COPY services/terminal-daemon/package.json ./
# Allow scripts so node-pty can build native bindings; disable audit/fund noise
RUN npm install --no-audit --no-fund

# Build daemon
COPY services/terminal-daemon/tsconfig.json ./
COPY services/terminal-daemon/src ./src
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY services/terminal-daemon/package.json ./
EXPOSE 8080
CMD ["node","dist/server.js"]
