
FROM docker.io/node:18-slim

ENV HOST=0.0.0.0

ENV PORT=3000

ENV DATABASE_URL="file:/app/api/dev.db"

WORKDIR /app

RUN apt-get update -y && apt-get install -y openssl libssl-dev && rm -rf /var/lib/apt/lists/*

RUN groupadd --system api && useradd --system -g api api

COPY dist/api api

COPY src/prisma/schema.prisma api/prisma/schema.prisma

RUN chown -R api:api .

RUN npm --prefix api --omit=dev -f install

RUN cd api && npx prisma@4.16.1 generate --schema=prisma/schema.prisma

RUN cd api && npx prisma@4.16.1 db push --schema=prisma/schema.prisma --skip-generate 2>/dev/null || true

USER api

CMD [ "node", "api" ]

