#!/bin/bash
set -e

echo "========================================="
echo "  Titanium - Ollama Model Setup"
echo "========================================="

OLLAMA_URL=${OLLAMA_BASE_URL:-http://localhost:11434}

check_ollama() {
    if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

pull_model() {
    local model=$1
    echo "Checking model: $model..."

    if curl -s "$OLLAMA_URL/api/tags" | grep -q "\"name\":\"$model\""; then
        echo "  ✓ $model already installed"
        return 0
    fi

    echo "  Downloading $model (this may take a while)..."
    curl -s -X POST "$OLLAMA_URL/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$model\", \"stream\": false}" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "  ✓ $model installed successfully"
    else
        echo "  ✗ Failed to install $model"
        return 1
    fi
}

echo ""
echo "Checking Ollama connection at $OLLAMA_URL..."

if ! check_ollama; then
    echo "✗ Ollama is not running at $OLLAMA_URL"
    echo ""
    echo "Start Ollama with:"
    echo "  ollama serve"
    echo ""
    echo "Or set OLLAMA_BASE_URL environment variable"
    exit 1
fi

echo "✓ Ollama is running"
echo ""
echo "Installing required models..."
echo ""

pull_model "llama3"
pull_model "nomic-embed-text"

echo ""
echo "========================================="
echo "  Models ready!"
echo "========================================="
echo ""
echo "Available models:"
curl -s "$OLLAMA_URL/api/tags" | python3 -m json.tool 2>/dev/null || echo "  (unable to list)"
