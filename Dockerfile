# Multi-stage: Hugo build → nginx + Flask Admin
FROM klakegg/hugo:0.148.2-ext-alpine AS hugo
WORKDIR /src
COPY . .
RUN hugo --minify --gc

FROM python:3.12-slim AS admin
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=hugo /src/public /app/public
COPY admin_server.py image_generation.py ./
COPY static/ /app/static/
COPY content/ /app/content/
COPY config.toml .
EXPOSE 5000
ENV FLASK_APP=admin_server.py
ENV EMINO_BLOG_DIR=/app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "admin_server:app"]

FROM node:22-alpine AS web-mcp
WORKDIR /app
RUN apk add --no-cache hugo
COPY web-mcp/package.json web-mcp/package-lock.json ./
RUN npm ci --omit=dev
COPY web-mcp/src ./src
COPY web-mcp/public ./public
EXPOSE 8787
ENV HOST=0.0.0.0
ENV WEB_MCP_ROOT=/site
CMD ["node", "src/http.mjs"]

FROM nginx:alpine AS final
COPY --from=hugo /src/public /usr/share/nginx/html
COPY nginx-default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
