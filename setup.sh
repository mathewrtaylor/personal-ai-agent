#!/bin/bash
# setup.sh - Personal AI Agent Setup Script

set -e

echo "🤖 Personal AI Agent Setup"
echo "=========================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

print_status "Docker and Docker Compose are installed"

# Check Docker daemon and permissions
echo "🔍 Checking Docker permissions..."
if ! docker ps &> /dev/null; then
    print_error "Cannot connect to Docker daemon. This usually means permission issues."
    echo ""
    echo "To fix this, run:"
    echo "  chmod +x fix-docker-permissions.sh"
    echo "  ./fix-docker-permissions.sh"
    echo ""
    echo "Or manually add your user to the docker group:"
    echo "  sudo usermod -aG docker \$USER"
    echo "  # Then log out and log back in"
    echo ""
    read -p "Would you like to try running with sudo? (not recommended) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Using sudo for Docker commands..."
        DOCKER_CMD="sudo docker"
        COMPOSE_CMD="sudo docker-compose"
    else
        print_error "Please fix Docker permissions and run this script again."
        exit 1
    fi
else
    print_status "Docker permissions are correct"
    DOCKER_CMD="docker"
    # Try docker compose first (newer syntax), fall back to docker-compose
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    
    # Generate a secure secret key
    SECRET_KEY=""
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -hex 32)
    elif command -v python3 &> /dev/null; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "")
    fi
    
    if [ -n "$SECRET_KEY" ]; then
        # Replace placeholder with generated key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/change-this-to-a-secure-random-string-in-production/$SECRET_KEY/" .env
        else
            # Linux
            sed -i "s/change-this-to-a-secure-random-string-in-production/$SECRET_KEY/" .env
        fi
        print_status "Created .env file with generated secret key"
    else
        print_warning "Created .env file but could not generate secret key automatically"
        print_info "Please edit .env and set a secure SECRET_KEY"
    fi
    
    print_info "Please review and customize the .env file for your needs"
else
    print_status ".env file already exists"
fi

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p backend/app/{api,core,models,services}
mkdir -p frontend/src/{components/Chat,components/Settings,services,hooks,utils}
mkdir -p frontend/public

print_status "Created directory structure"

# Ask user about model preference
echo ""
echo "🧠 AI Model Configuration"
echo "========================"
echo "Choose your AI model provider:"
echo "1) Ollama (Local, Private, Free - Recommended)"
echo "2) OpenAI (Requires API key, Paid)"  
echo "3) Anthropic (Requires API key, Paid)"
echo ""

read -p "Enter your choice (1-3) [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo "📦 Configuring for Ollama..."
        # Update .env for Ollama
        sed -i 's/MODEL_PROVIDER=.*/MODEL_PROVIDER=ollama/' .env 2>/dev/null || true
        print_status "Ollama will be used (models will be downloaded on first run)"
        EXPECTED_DOWNLOAD="yes"
        ;;
    2)
        echo "🔑 Configuring for OpenAI..."
        read -p "Enter your OpenAI API key: " openai_key
        if [ -n "$openai_key" ]; then
            sed -i 's/MODEL_PROVIDER=.*/MODEL_PROVIDER=openai/' .env 2>/dev/null || true
            sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env 2>/dev/null || true
            print_status "OpenAI configured"
        else
            print_error "No API key provided. Please edit .env file manually."
        fi
        ;;
    3)
        echo "🔑 Configuring for Anthropic..."
        read -p "Enter your Anthropic API key: " anthropic_key
        if [ -n "$anthropic_key" ]; then
            sed -i 's/MODEL_PROVIDER=.*/MODEL_PROVIDER=anthropic/' .env 2>/dev/null || true
            sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$anthropic_key/" .env 2>/dev/null || true
            print_status "Anthropic configured"
        else
            print_error "No API key provided. Please edit .env file manually."
        fi
        ;;
    *)
        print_warning "Invalid choice, defaulting to Ollama"
        sed -i 's/MODEL_PROVIDER=.*/MODEL_PROVIDER=ollama/' .env 2>/dev/null || true
        EXPECTED_DOWNLOAD="yes"
        ;;
esac

# Build and start services
echo ""
echo "🚀 Starting Personal AI Agent..."
echo "================================"

echo "📦 Building Docker images..."
if ! $COMPOSE_CMD build; then
    print_error "Failed to build Docker images"
    exit 1
fi

echo "🏃 Starting services..."
if ! $COMPOSE_CMD up -d; then
    print_error "Failed to start services"
    print_info "Check logs with: $COMPOSE_CMD logs"
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
if $COMPOSE_CMD ps | grep -q "Up"; then
    print_status "Services are starting up!"
    echo ""
    echo "🎉 Personal AI Agent Setup Complete!"
    echo "===================================="
    echo ""
    echo "Your AI agent is now running at:"
    echo "• ${BLUE}Frontend (Chat UI):${NC} http://localhost:3000"
    echo "• ${BLUE}Backend API:${NC} http://localhost:8000" 
    echo "• ${BLUE}API Documentation:${NC} http://localhost:8000/docs"
    echo ""
    
    if [ "$EXPECTED_DOWNLOAD" = "yes" ]; then
        print_warning "First run with Ollama will download the model (~4GB)"
        echo "This may take a few minutes depending on your internet connection."
        echo "You can monitor the download with: $COMPOSE_CMD logs -f ollama"
        echo ""
    fi
    
    echo "🔧 Useful commands:"
    echo "• View logs: $COMPOSE_CMD logs -f"
    echo "• Stop services: $COMPOSE_CMD down"  
    echo "• Restart: $COMPOSE_CMD restart"
    echo "• Update: git pull && $COMPOSE_CMD build && $COMPOSE_CMD up -d"
    echo ""
    
    # Check for common issues
    echo "🔍 Running quick health checks..."
    sleep 5
    
    if curl -f http://localhost:8000/api/health &>/dev/null; then
        print_status "Backend API is responding"
    else
        print_warning "Backend API not responding yet (may still be starting up)"
        print_info "Check backend logs: $COMPOSE_CMD logs backend"
    fi
    
    if curl -f http://localhost:3000 &>/dev/null; then
        print_status "Frontend is responding"
    else
        print_warning "Frontend not responding yet (may still be starting up)"
        print_info "Check frontend logs: $COMPOSE_CMD logs frontend"
    fi
    
    echo ""
    print_info "📚 For more information, see the README.md file"
    print_info "🐛 If you encounter issues, check logs with: $COMPOSE_CMD logs [service-name]"
    
else
    print_error "Some services failed to start. Check logs with:"
    echo "$COMPOSE_CMD logs"
    echo ""
    print_info "Common issues:"
    echo "1. Port conflicts - make sure ports 3000, 8000, 5432, 11434 are free"
    echo "2. Insufficient resources - Ollama needs at least 4GB RAM"
    echo "3. Docker permissions - run ./fix-docker-permissions.sh"
fi