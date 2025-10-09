# web_frontend/Dockerfile
FROM nginx:1.27-alpine

# Copiar estáticos al docroot
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY main.js /usr/share/nginx/html/main.js

# Config Nginx con reverse proxy /api → api:8000
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
