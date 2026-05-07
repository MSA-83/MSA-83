#!/bin/bash
set -e

echo "========================================="
echo "  Titanium Deployment Script"
echo "========================================="

ENVIRONMENT=${1:-development}
echo "Environment: $ENVIRONMENT"

case $ENVIRONMENT in
  development)
    echo ""
    echo "Starting development stack..."
    docker compose up -d
    echo ""
    echo "Services:"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  Ollama:    http://localhost:11434"
    echo "  Qdrant:    http://localhost:6333"
    echo "  Dashboard: http://localhost:6335"
    echo ""
    echo "Seeding memory..."
    python deployment/scripts/seed_memory.py
    ;;

  staging)
    echo ""
    echo "Building for staging..."
    docker compose -f docker-compose.yml -f docker-compose.staging.yml build
    docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
    echo "Staging deployed"
    ;;

  production)
    echo ""
    echo "Production deployment via CI/CD"
    echo "Push to main branch to trigger deployment"
    ;;

  kubernetes)
    echo ""
    echo "Deploying to Kubernetes..."
    kubectl apply -f infra/k8s/namespace.yaml
    kubectl apply -f infra/k8s/qdrant.yaml
    kubectl apply -f infra/k8s/backend.yaml
    kubectl apply -f infra/k8s/frontend.yaml
    kubectl apply -f infra/k8s/ingress.yaml
    echo "Kubernetes deployment complete"
    ;;

  *)
    echo "Usage: $0 {development|staging|production|kubernetes}"
    exit 1
    ;;
esac

echo ""
echo "========================================="
echo "  Deployment complete"
echo "========================================="
