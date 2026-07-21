FROM python:3.11-slim

# System deps — use Debian Trixie package names (python:3.11-slim base)
# libgl1-mesa-glx was renamed to libgl1 in Trixie
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-create directories
RUN mkdir -p /app/ai_models/saved /app/data/processed /app/reports

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
