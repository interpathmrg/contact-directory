# Stage 1: Build React
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --silent

COPY . .
RUN npm run build

# Stage 2: Serve con Nginx
FROM nginx:1.27-alpine

# Configuración de Nginx para SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar build de React
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
