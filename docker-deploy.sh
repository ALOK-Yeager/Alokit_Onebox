#!/usr/bin/env bash
# Build and Deploy Script for Onebox Aggregator Python Services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
IMAGE_NAME="onebox-aggregator"
DOCKERFILE="Dockerfile.python"
DOCKER_COMPOSE_FILE="docker-compose.python.yml"

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build [SERVICE]     Build Docker image(s)"
    echo "  run [SERVICE]       Run a specific service"
    echo "  start              Start all services with docker-compose"
    echo "  stop               Stop all services"
    echo "  restart            Restart all services"
    echo "  logs [SERVICE]     Show logs for service(s)"
    echo "  health             Check health of all services"
    echo "  clean              Clean up containers and images"
    echo ""
    echo "Services:"
    echo "  api-server         API Server (port 3000)"
    echo "  vectordb           VectorDB Service (port 8001)"
    echo "  api-gateway        API Gateway (port 3001)"
    echo ""
    echo "Examples:"
    echo "  $0 build api-server     # Build API server image"
    echo "  $0 run vectordb         # Run VectorDB service"
    echo "  $0 start                # Start all services"
    echo "  $0 logs api-gateway     # Show gateway logs"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to build a specific service
build_service() {
    local service=$1
    local script_map=(
        ["api-server"]="api_server.py"
        ["vectordb"]="vectordb_service.py"
        ["api-gateway"]="api_gateway_onebox.py"
    )
    
    if [[ -z "${script_map[$service]}" ]]; then
        print_error "Unknown service: $service"
        echo "Available services: ${!script_map[@]}"
        exit 1
    fi
    
    local script=${script_map[$service]}
    local tag="$IMAGE_NAME:$service"
    
    print_status "Building $service image ($tag)..."
    
    docker build \
        -f "$DOCKERFILE" \
        --build-arg SERVICE_SCRIPT="$script" \
        -t "$tag" \
        .
    
    print_success "$service image built successfully!"
}

# Function to build all services
build_all() {
    print_status "Building all service images..."
    
    build_service "vectordb"
    build_service "api-server" 
    build_service "api-gateway"
    
    print_success "All images built successfully!"
}

# Function to run a specific service
run_service() {
    local service=$1
    local port_map=(
        ["api-server"]="3000:3000"
        ["vectordb"]="8001:8001"
        ["api-gateway"]="3001:3001"
    )
    
    if [[ -z "${port_map[$service]}" ]]; then
        print_error "Unknown service: $service"
        echo "Available services: ${!port_map[@]}"
        exit 1
    fi
    
    local ports=${port_map[$service]}
    local tag="$IMAGE_NAME:$service"
    local container_name="onebox-$service"
    
    print_status "Running $service container..."
    
    # Stop and remove existing container if it exists
    docker stop "$container_name" 2>/dev/null || true
    docker rm "$container_name" 2>/dev/null || true
    
    # Run the container
    docker run -d \
        --name "$container_name" \
        -p "$ports" \
        --env-file .env 2>/dev/null || \
        docker run -d \
            --name "$container_name" \
            -p "$ports" \
            "$tag"
    
    print_success "$service is running on port ${ports%:*}!"
    print_status "Container logs: docker logs $container_name"
}

# Function to start all services with docker-compose
start_all() {
    print_status "Starting all services with docker-compose..."
    
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        print_error "Docker compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    print_success "All services started!"
    print_status "Services are starting up. Use '$0 health' to check status."
}

# Function to stop all services
stop_all() {
    print_status "Stopping all services..."
    
    if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
    fi
    
    # Also stop any individually started containers
    docker stop onebox-api-server onebox-vectordb onebox-api-gateway 2>/dev/null || true
    
    print_success "All services stopped!"
}

# Function to restart all services
restart_all() {
    print_status "Restarting all services..."
    stop_all
    start_all
}

# Function to show logs
show_logs() {
    local service=$1
    
    if [[ -z "$service" ]]; then
        print_status "Showing logs for all services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
    else
        print_status "Showing logs for $service..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f "$service"
    fi
}

# Function to check health of services
check_health() {
    print_status "Checking service health..."
    
    local services=("api-server:3000" "vectordb:8001" "api-gateway:3001")
    
    for service_port in "${services[@]}"; do
        local service=${service_port%:*}
        local port=${service_port#*:}
        
        print_status "Checking $service (port $port)..."
        
        if curl -f -s "http://localhost:$port/health" >/dev/null; then
            print_success "$service is healthy ✓"
        else
            print_warning "$service is not responding ✗"
        fi
    done
}

# Function to clean up containers and images
clean_up() {
    print_warning "This will remove all Onebox containers and images. Continue? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_status "Cleaning up containers and images..."
        
        # Stop and remove containers
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v 2>/dev/null || true
        docker stop onebox-api-server onebox-vectordb onebox-api-gateway 2>/dev/null || true
        docker rm onebox-api-server onebox-vectordb onebox-api-gateway 2>/dev/null || true
        
        # Remove images
        docker rmi "$IMAGE_NAME:api-server" "$IMAGE_NAME:vectordb" "$IMAGE_NAME:api-gateway" 2>/dev/null || true
        
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Main script logic
main() {
    check_docker
    
    case "${1:-}" in
        "build")
            if [[ -n "${2:-}" ]]; then
                build_service "$2"
            else
                build_all
            fi
            ;;
        "run")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required for run command"
                show_usage
                exit 1
            fi
            build_service "$2"
            run_service "$2"
            ;;
        "start")
            start_all
            ;;
        "stop")
            stop_all
            ;;
        "restart")
            restart_all
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "health")
            check_health
            ;;
        "clean")
            clean_up
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        "")
            print_error "No command specified"
            show_usage
            exit 1
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"