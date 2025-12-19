FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# 빌드 시점에 환경변수가 필요한 경우 여기서 정의 가능
# ENV NEXT_PUBLIC_API_URL=http://localhost:8000

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]