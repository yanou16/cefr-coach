#!/bin/bash
set -e

echo "[startup] CEFR Coach API starting..."

# Build ChromaDB index from corpus if empty
python -c "
import sys
sys.path.insert(0, '.')
from app.services.rag_service import build_index, _get_collection
col = _get_collection()
if col.count() == 0:
    print('[startup] ChromaDB empty — building index from corpus...')
    n = build_index(force=False)
    print(f'[startup] Indexed {n} chunks OK')
else:
    print(f'[startup] ChromaDB has {col.count()} chunks — skipping build')
"

# Render injects $PORT automatically; fall back to 8001 for local dev
PORT=${PORT:-8001}
echo "[startup] Starting uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
