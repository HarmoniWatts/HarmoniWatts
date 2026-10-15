# Frontend Angular — desarrollo con ng serve (npm start)
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 4200

# --host 0.0.0.0: accesible desde el host; --poll: hot reload fiable en Docker/Windows
CMD ["npm", "start", "--", "--host", "0.0.0.0", "--port", "4200", "--poll", "2000"]
