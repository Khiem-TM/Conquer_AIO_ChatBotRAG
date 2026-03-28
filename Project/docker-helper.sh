#!/bin/bash
# RAG Chatbot Docker Helper Script
# This script provides convenient Docker deployment commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$SCRIPT_DIR/docker"

# Functions
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi
    print_success "Docker found"
    return 0
}

check_requirements() {
    print_info "Checking requirements.txt..."
    if ! grep -q "qdrant-client" "$PROJECT_DIR/requirements.txt"; then
        print_error "qdrant-client not found in requirements.txt"
        return 1
    fi
    print_success "requirements.txt looks good"
    return 0
}

fix_docker_credentials() {
    print_info "Fixing Docker credentials (macOS)..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ -f ~/.docker/config.json ]; then
            cp ~/.docker/config.json ~/.docker/config.json.bak
            print_info "Backed up config to ~/.docker/config.json.bak"
        fi
        
        cat > ~/.docker/config.json << 'EOF'
{
  "auths": {},
  "currentContext": "desktop-linux"
}
EOF
        print_success "Docker config updated"
    else
        print_warning "Not on macOS, skipping credential fix"
    fi
}

build_images() {
    print_info "Building Docker images..."
    cd "$DOCKER_DIR"
    docker compose build
    print_success "Build complete"
}

start_services() {
    print_info "Starting services..."
    cd "$DOCKER_DIR"
    docker compose up -d
    print_success "Services started"
    
    print_info "Waiting for services to be ready..."
    sleep 5
    
    check_health
}

stop_services() {
    print_info "Stopping services..."
    cd "$DOCKER_DIR"
    docker compose down
    print_success "Services stopped"
}

check_health() {
    print_info "Checking service health..."
    
    # Check API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API is healthy (http://localhost:8000)"
    else
        print_warning "API health check failed"
    fi
    
    # Check Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama is running (http://localhost:11434)"
    else
        print_warning "Ollama health check failed"
    fi
}

view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        service="api"
    fi
    print_info "Viewing logs for $service..."
    cd "$DOCKER_DIR"
    docker compose logs -f "$service"
}

status() {
    print_info "Service status:"
    cd "$DOCKER_DIR"
    docker compose ps
}

clean() {
    print_warning "Cleaning up Docker resources..."
    read -p "This will remove containers and images. Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$DOCKER_DIR"
        docker compose down -v
        docker image rm -f rag-chatbot-api docker-api 2>/dev/null || true
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

pull_ollama_model() {
    print_info "Pulling Ollama model..."
    docker exec rag-chatbot-ollama ollama pull llama3.1:8b
    print_success "Model pulled"
}

test_api() {
    print_info "Testing API endpoints..."
    
    print_info "Testing health endpoint..."
    curl -s http://localhost:8000/health | jq . || print_error "Health check failed"
    
    print_info "Testing chat endpoint..."
    curl -s -X POST http://localhost:8000/api/v1/chat \
        -H "Content-Type: application/json" \
        -d '{"question": "What is RAG?"}' | jq . || print_error "Chat endpoint failed"
}

rebuild() {
    print_warning "Performing clean rebuild..."
    cd "$DOCKER_DIR"
    docker compose down
    docker image rm -f rag-chatbot-api 2>/dev/null || true
    docker compose build --no-cache
    docker compose up -d
    print_success "Rebuild complete"
}

help_message() {
    cat << EOF
${BLUE}RAG Chatbot Docker Helper${NC}

Usage: $0 <command> [options]

Commands:
    check           Check system prerequisites
    fix-creds       Fix Docker credentials (macOS)
    build           Build Docker images
    start           Start all services
    stop            Stop all services
    status          Show service status
    logs [service]  View logs (default: api)
    health          Check service health
    test            Test API endpoints
    pull-model      Pull Ollama model
    rebuild         Clean rebuild (slow)
    clean           Remove all containers and images
    help            Show this help message

Examples:
    $0 check                # Check prerequisites
    $0 start                # Start services
    $0 logs api            # View API logs
    $0 logs ollama         # View Ollama logs
    $0 test                # Test endpoints
    $0 rebuild             # Clean rebuild

EOF
}

# Main script
main() {
    local command=${1:-help}
    
    case "$command" in
        check)
            check_docker && check_requirements
            ;;
        fix-creds)
            fix_docker_credentials
            ;;
        build)
            check_docker && build_images
            ;;
        start)
            check_docker && start_services
            ;;
        stop)
            stop_services
            ;;
        status)
            status
            ;;
        logs)
            view_logs "$2"
            ;;
        health)
            check_health
            ;;
        test)
            test_api
            ;;
        pull-model)
            pull_ollama_model
            ;;
        rebuild)
            rebuild
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            help_message
            ;;
        *)
            print_error "Unknown command: $command"
            help_message
            exit 1
            ;;
    esac
}

main "$@"
