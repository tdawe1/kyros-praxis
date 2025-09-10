FROM node:20-alpine

RUN apk add --no-cache git python3 make g++

WORKDIR /app

# Clone and build Fireproof MCP server
RUN git clone --depth 1 https://github.com/fireproof-storage/mcp-database-server.git . 
RUN npm ci \
 && npm run build

ENTRYPOINT ["node","build/index.js"]

