FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user (HF Spaces requirement)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY model.py .
COPY app.py .

# Copy the pre-built React frontend
COPY static/ ./static/

# Copy data assets (demo images, figures, report)
COPY data/ ./data/

# The model checkpoint will be downloaded from HF Hub at runtime
# Set environment variables
ENV HF_HOME=/home/user/.cache/huggingface
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
RUN chown -R user:user /home/user
USER user

EXPOSE 7860

# Start with gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--timeout", "300", "--workers", "1", "--threads", "4"]
