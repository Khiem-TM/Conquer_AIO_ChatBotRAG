#!/bin/bash

# RAG ChatBot Docker Setup Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$PROJECT_DIR/docker"

echo "=================================================="
echo "  RAG ChatBot - Docker Compose Setup"
echo "=================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✓ Docker found: $(docker --version)"
echo ""

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker Compose available"
echo ""

# Get command from arguments
COMMAND=${1:-up}

case "$COMMAND" in
    up)
        echo "🚀 Starting RAG ChatBot services..."
        cd "$DOCKER_DIR"
        docker-compose up -d
        echo ""
        echo "✓ Services started!"
        echo ""
        echo "Available services:"
        echo "  - Backend API: http://localhost:8000"
        echo "  - Ollama: http://localhost:11434"
        echo "  - Frontend: http://localhost:3001"
        echo ""
        echo "📋 Logs:"
        docker-compose logs -f
        ;;
    
    down)
        echo "🛑 Stopping RAG ChatBot services..."
        cd "$DOCKER_DIR"
        docker-compose down
        echo "✓ Services stopped"
        ;;
    
    restart)
        echo "🔄 Restarting RAG ChatBot services..."
        cd "$DOCKER_DIR"
        docker-compose restart
        echo "✓ Services restarted"
        ;;
    
    logs)
        echo "📋 Service logs:"
        cd "$DOCKER_DIR"
        docker-compose logs -f ${2:-}
        ;;
    
    status)
        echo "📊 Service status:"
        cd "$DOCKER_DIR"
        docker-compose ps
        ;;
    
    build)
        echo "🔨 Building Docker images..."
        cd "$DOCKER_DIR"
        docker-compose build
        echo "✓ Build complete"
        ;;
    
    clean)
        echo "🧹 Cleaning up Docker resources..."
        cd "$DOCKER_DIR"
        docker-compose down -v
        echo "✓ Cleanup complete"
        ;;
    
    help)
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  up       - Start all services (default)"
        echo "  down     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - View service logs"
        echo "  status   - Show service status"
        echo "  build    - Build Docker images"
        echo "  clean    - Clean up all containers and volumes"
        echo "  help     - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 up           # Start services"
        echo "  $0 logs api     # View API logs"
        echo "  $0 logs ollama  # View Ollama logs"
        ;;
    
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
