# Docker Compose Configuration Adjustments

This document covers common adjustments you may need to make to the `docker-compose.yml` file for your specific environment and requirements.

## Timezone Configuration

**Issue**: Timestamps in chat messages appear in UTC instead of your local timezone.

**Solution**: Add timezone environment variables to your services:

```yaml
services:
  backend:
    environment:
      - TZ=${TZ:-UTC}  # Use host timezone or UTC as fallback
      # ... other environment variables
    volumes:
      - /etc/localtime:/etc/localtime:ro  # Mount host timezone
      
  frontend:
    environment:
      - TZ=${TZ:-UTC}  # Use host timezone
      # ... other environment variables
    volumes:
      - /etc/localtime:/etc/localtime:ro  # Mount host timezone
```

Then add your timezone to `.env`:
```bash
# Find your timezone
timedatectl show --property=Timezone --value

# Add to .env file
echo "TZ=America/New_York" >> .env  # Replace with your timezone
```

## Port Conflicts

**Issue**: Ports 3000, 8000, 5432, or 11434 are already in use on your system.

**Solution**: Change the port mappings in `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # Change host port (left side)
      
  backend:
    ports:
      - "8001:8000"  # Change host port (left side)
      
  postgres:
    ports:
      - "5433:5432"  # Change host port (left side)
      
  ollama:
    ports:
      - "11435:11434"  # Change host port (left side)
```

If you change the backend port, also update the frontend environment:
```yaml
  frontend:
    environment:
      - REACT_APP_API_URL=http://localhost:8001  # Match new backend port
```

## GPU Support for Ollama

**Issue**: Want to use GPU acceleration for faster AI responses.

**Solution**: Uncomment and configure GPU support for Ollama:

```yaml
  ollama:
    # ... existing configuration
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Prerequisites**: 
- NVIDIA GPU with CUDA support
- nvidia-docker2 installed
- NVIDIA Container Toolkit configured

## Memory and Resource Limits

**Issue**: Containers using too much memory or need resource limits.

**Solution**: Add resource limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          
  ollama:
    deploy:
      resources:
        limits:
          memory: 4G  # Ollama needs more memory for models
          cpus: '2.0'
        reservations:
          memory: 2G
```

## Alternative AI Providers

**Issue**: Want to use OpenAI or Anthropic instead of local Ollama.

**Solution**: 

1. Update your `.env` file:
```bash
# For OpenAI
MODEL_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here

# For Anthropic
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
```

2. Optionally disable Ollama service:
```yaml
  ollama:
    # ... existing configuration
    profiles:
      - local-only  # Only start when using --profile local-only
```

## Production Deployment

**Issue**: Need to deploy for production use.

**Solution**: Use the production profile:

```bash
# Start with production services (includes nginx)
docker-compose --profile production up -d
```

Update environment variables for production:
```yaml
  backend:
    environment:
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}  # Use a secure secret key
      # Remove wildcard CORS origins for security
```

## Persistent Data Location

**Issue**: Want to store data in a specific location.

**Solution**: Use bind mounts instead of Docker volumes:

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/your/data/postgres  # Your preferred path
      
  ollama_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/your/data/ollama    # Your preferred path
```

Create the directories first:
```bash
mkdir -p /path/to/your/data/{postgres,ollama}
```

## Network Configuration

**Issue**: Need custom network configuration or multiple instances.

**Solution**: Customize the network:

```yaml
networks:
  aiagent-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16  # Custom subnet
```

For multiple instances, use different network names and port ranges.

## Development vs Production

**Issue**: Need different configurations for development and production.

**Solution**: Use multiple compose files:

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production  
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Create `docker-compose.dev.yml`:
```yaml
services:
  backend:
    volumes:
      - ./backend:/app  # Enable code reloading
  frontend:
    volumes:
      - ./frontend:/app  # Enable code reloading
```

Create `docker-compose.prod.yml`:
```yaml
services:
  backend:
    environment:
      - DEBUG=false
    volumes: []  # Remove development volumes
  frontend:
    build:
      target: production  # Use production build
    volumes: []  # Remove development volumes
```

## Troubleshooting

### Services Won't Start

1. Check port conflicts: `netstat -tlnp | grep -E "(3000|8000|5432|11434)"`
2. Check Docker daemon: `docker ps`
3. Check logs: `docker-compose logs [service-name]`

### Permission Issues

1. Fix Docker permissions: `sudo usermod -aG docker $USER`
2. Log out and back in
3. Check file permissions in mounted volumes

### Database Issues

1. Reset database: `docker-compose down -v` (WARNING: Deletes all data)
2. Check database logs: `docker-compose logs postgres`
3. Verify connection: `docker-compose exec postgres psql -U aiagent -d aiagent -c "\dt"`

### Model Download Issues

1. Check Ollama logs: `docker-compose logs ollama`
2. Manual model pull: `docker-compose exec ollama ollama pull llama3.2`
3. Check available models: `docker-compose exec ollama ollama list`