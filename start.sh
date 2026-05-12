#!/bin/bash
# SaaS uygulamasını başlatır: backend (8000) + frontend (3000)

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv/bin"
API_DIR="$ROOT/apps/api"
WEB_DIR="$ROOT/apps/web"

echo "🔄 Cache temizleniyor..."
find "$API_DIR" -name "*.pyc" -delete 2>/dev/null
find "$API_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "🚀 Backend başlatılıyor (port 8000)..."
PYTHONPATH="$API_DIR" "$VENV/uvicorn" app.main:app --reload --port 8000 --app-dir "$API_DIR" &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

echo "🌐 Frontend başlatılıyor (port 3000)..."
cd "$WEB_DIR" && npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ Hazır!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Durdurmak için: kill $BACKEND_PID $FRONTEND_PID"

wait
