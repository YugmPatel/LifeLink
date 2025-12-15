# Dockerfile for Streamlit MLOps Dashboard
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ml_pipeline/requirements_ml.txt requirements_ml.txt
RUN pip install --no-cache-dir -r requirements_ml.txt

# Copy application files
COPY evaluation/ evaluation/
COPY ml_pipeline/ ml_pipeline/
COPY data/ data/
COPY artifacts/ artifacts/
# Environment variables will be set via Cloud Run

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "evaluation/streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]