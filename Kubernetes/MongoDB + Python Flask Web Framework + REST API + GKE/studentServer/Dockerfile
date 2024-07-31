FROM node:14
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY studentServer.js ./
EXPOSE 8080
ENTRYPOINT ["node", "studentServer.js"]