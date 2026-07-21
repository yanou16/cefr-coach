#!/bin/bash
set -e

echo "[startup] CEFR Coach API starting..."

# Build ChromaDB index from corpus if empty (first boot only)
python -c "
import os, sys
sys.path.insert(0, '/app')
from app.services.rag_service import build_index, _get_collection
col = _get_collection()
if col.count() == 0:
    print('[startup] ChromaDB empty — building index from corpus...')
    n = build_index(force=False)
    print(f'[startup] Indexed {n} chunks OK')
else:
    print(f'[startup] ChromaDB already has {col.count()} chunks — skipping build')
"

echo "[startup] Starting uvicorn on port 7860..."
exec uvicorn app.main:app --host 0.0.0.0 --port 7860
