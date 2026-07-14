# Build stage
FROM node:22-slim AS build

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Baked at build time (Vite inlines import.meta.env)
ARG VITE_GOOGLE_CLIENT_ID=""
ENV VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID}

RUN npm run build

# Serve stage
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html

EXPOSE 80
