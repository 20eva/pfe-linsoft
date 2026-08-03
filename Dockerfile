FROM docker.io/node:lts-alpine
ENV HOST=0.0.0.0
ENV PORT=3000
ENV DATABASE_URL="file:/app/api/dev.db"
WORKDIR /app
RUN addgroup --system api && adduser --system -G api api
COPY dist/api api
RUN chown -R api:api .
RUN npm --prefix api --omit=dev -f install
RUN cd api && npx prisma generate && npx prisma db push --skip-generate 2>/dev/null || true
USER api
CMD [ "node", "api" ]
