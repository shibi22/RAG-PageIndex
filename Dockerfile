FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if required by audio processing or other tools
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the workspace directory exists
RUN mkdir -p /app/workspace

# Expose the FastAPI port
EXPOSE 8000

# Set environment variables for production
ENV PYTHONPATH=/app
ENV WORKSPACE_DIR=/app/workspace

# Run the Uvicorn server
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
