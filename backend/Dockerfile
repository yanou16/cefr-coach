# HuggingFace Spaces — CEFR Coach FastAPI backend
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Lean prod requirements (no torch, no ragas, no langfuse)
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# App source + corpus
COPY app/ ./app/
COPY corpus/ ./corpus/
COPY startup.sh .
RUN chmod +x startup.sh

# HF Spaces persistent storage at /data
# ChromaDB index is built there on first boot, persists across restarts
ENV CHROMA_DIR=/data/chroma_db

EXPOSE 7860

CMD ["./startup.sh"]
