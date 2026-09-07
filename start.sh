#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env.local exists
if [ ! -f .env.local ]; then
  echo "Creating .env.local from .env.example..."
  cp .env.example .env.local
  echo "Please edit .env.local and add your GEMINI_API_KEY"
fi

# Start backend in background
echo -e "${BLUE}Starting FastAPI backend...${NC}"
cd backend
if [ -x "../.venv/bin/python" ]; then
  ../.venv/bin/python -m uvicorn main:app --reload --port 8000 &
elif command -v uv >/dev/null 2>&1; then
  uv run python -m uvicorn main:app --reload --port 8000 &
else
  python3 -m uvicorn main:app --reload --port 8000 &
fi
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 2

# Start frontend
echo -e "${BLUE}Starting Next.js frontend...${NC}"
if command -v pnpm >/dev/null 2>&1; then
  pnpm dev &
else
  npm run dev &
fi
FRONTEND_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

echo -e "${GREEN}QueryLens is starting!${NC}"
echo -e "${GREEN}Backend: http://localhost:8000${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}API Docs: http://localhost:8000/docs${NC}"

# Wait for both processes
wait
