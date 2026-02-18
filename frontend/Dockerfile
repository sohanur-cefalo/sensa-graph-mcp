FROM node:20-alpine

WORKDIR /app

# Accept build arguments from docker-compose and set as environment variables for Vite build
ARG VITE_NEO4J_URI
ARG VITE_NEO4J_USER
ARG VITE_NEO4J_PASSWORD
ARG VITE_API_BASE_URL
ARG VITE_GRAPH_SOURCE

ENV VITE_NEO4J_URI=$VITE_NEO4J_URI
ENV VITE_NEO4J_USER=$VITE_NEO4J_USER
ENV VITE_NEO4J_PASSWORD=$VITE_NEO4J_PASSWORD
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_GRAPH_SOURCE=$VITE_GRAPH_SOURCE

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application (with output)
RUN echo "Building frontend application..." && \
    npm run build && \
    echo "Build completed successfully!"

# Expose Vite preview port
EXPOSE 3000

# Start Vite preview server with verbose logging
# Using sh -c to ensure proper output redirection
CMD sh -c "echo 'Starting Vite preview server on port 3000...' && npx vite preview --host 0.0.0.0 --port 3000 --logLevel info"
