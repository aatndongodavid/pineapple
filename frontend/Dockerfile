FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-timeout 600000 && \
    npm install --include=dev

COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/html/maintenance.html /usr/share/nginx/html/maintenance.html

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
