# ─────────────────────────────────────────────
# AIOps Predictor — Docker image
# Used for OKD deployment (Option B)
# ─────────────────────────────────────────────

FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (better Docker cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY extractor/     ./extractor/
COPY model/         ./model/
COPY api/           ./api/
COPY ci_scanner/    ./ci_scanner/

# Expose the FastAPI port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
