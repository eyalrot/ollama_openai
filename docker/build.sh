#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BUILD_TYPE="prod"
PUSH=false
REGISTRY=""
TAG="latest"

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -t, --type      Build type: prod or dev (default: prod)"
    echo "  -p, --push      Push to registry after build"
    echo "  -r, --registry  Docker registry (e.g., docker.io/username)"
    echo "  -g, --tag       Docker image tag (default: latest)"
    echo "  -h, --help      Show this help message"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -g|--tag)
            TAG="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Validate build type
if [[ "$BUILD_TYPE" != "prod" && "$BUILD_TYPE" != "dev" ]]; then
    echo -e "${RED}Invalid build type: $BUILD_TYPE${NC}"
    usage
fi

# Set variables based on build type
if [[ "$BUILD_TYPE" == "prod" ]]; then
    DOCKERFILE="docker/Dockerfile.prod"
    IMAGE_NAME="ollama-openai-proxy"
else
    DOCKERFILE="docker/Dockerfile.dev"
    IMAGE_NAME="ollama-openai-proxy-dev"
fi

# Add registry prefix if provided
if [[ -n "$REGISTRY" ]]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"
else
    FULL_IMAGE_NAME="$IMAGE_NAME"
fi

echo -e "${GREEN}Building $BUILD_TYPE image...${NC}"
echo "Dockerfile: $DOCKERFILE"
echo "Image: $FULL_IMAGE_NAME:$TAG"

# Enable BuildKit for better caching
export DOCKER_BUILDKIT=1

# Build the image
docker build \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    -f "$DOCKERFILE" \
    -t "$FULL_IMAGE_NAME:$TAG" \
    -t "$FULL_IMAGE_NAME:$BUILD_TYPE-$(date +%Y%m%d-%H%M%S)" \
    .

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}Build successful!${NC}"
    
    # Show image info
    echo -e "\n${YELLOW}Image info:${NC}"
    docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    
    # Push if requested
    if [[ "$PUSH" == true ]]; then
        if [[ -z "$REGISTRY" ]]; then
            echo -e "${RED}Registry must be specified when pushing${NC}"
            exit 1
        fi
        
        echo -e "\n${GREEN}Pushing image to registry...${NC}"
        docker push "$FULL_IMAGE_NAME:$TAG"
        docker push "$FULL_IMAGE_NAME:$BUILD_TYPE-$(date +%Y%m%d-%H%M%S)"
    fi
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi