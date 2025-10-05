FROM node:20-alpine AS builder
WORKDIR /app

# Copy manifests and install deps
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build Next.js (src/app)
ENV NEXT_DISABLE_ESLINT=1
ENV NEXT_DISABLE_TYPE_CHECK=1
RUN npx next build --no-lint

# Production image
FROM node:20-alpine
WORKDIR /app

# Copy package files
COPY --from=builder /app/package*.json ./

# Install only production dependencies
RUN npm ci --omit=dev

# Copy Next.js build output
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Copy application source
COPY --from=builder /app/src ./src

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

CMD ["npm", "start"]