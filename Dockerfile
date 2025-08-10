# Node.js runtime for TypeScript app
FROM node:22-slim

WORKDIR /workspace

COPY package.json package-lock.json* tsconfig.json ./
RUN npm ci || npm i

COPY src ./src
COPY public ./public
COPY config ./config

RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "serve"]
