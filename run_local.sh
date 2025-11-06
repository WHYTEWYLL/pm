#!/bin/bash
# Run PM Assistant locally with existing env vars

echo "🚀 Starting PM Assistant (Local Dev Mode)"
echo ""

# Set local dev environment
export ENV=development
export DEV_TENANT_ID=local-dev-tenant

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Using environment variables."
fi

echo "📦 Setting up local tenant..."
python3 -c "
import requests
import time
time.sleep(2)  # Wait for server to start
try:
    response = requests.post('http://localhost:8000/api/local-dev/setup-tenant')
    print('✅ Local tenant setup:', response.json())
except Exception as e:
    print('⚠️  Could not setup tenant (server may not be ready):', e)
" &

echo "🌐 Starting API server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "💡 To test workflows:"
echo "   curl http://localhost:8000/api/workflows/ingest/slack"
echo "   curl http://localhost:8000/api/workflows/ingest/linear"
echo ""

uvicorn app.api.main:app --reload --port 8000

