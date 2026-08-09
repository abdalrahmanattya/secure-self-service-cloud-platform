# Release limitation: exact base tags are pinned; digest promotion is follow-up work.
FROM node:22.14.0-bookworm-slim AS builder

WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
RUN npm run build

FROM nginx:1.29.1-alpine

RUN addgroup -S -g 10001 platform \
    && adduser -S -D -H -u 10001 -G platform platform \
    && mkdir -p /var/cache/nginx /var/run /tmp/nginx \
    && chown -R platform:platform /var/cache/nginx /var/run /tmp/nginx /usr/share/nginx/html
COPY containers/portal/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder --chown=platform:platform /app/dist /usr/share/nginx/html
USER platform
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
