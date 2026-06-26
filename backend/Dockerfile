# Use an official lightweight Python image.
# We use python:3.11-slim because it's small but fully featured for scientific libraries.
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for compiling some scientific packages (e.g., C compiler for transitleastsquares)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Hugging Face Spaces requires this for security)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy the requirements file into the container
COPY --chown=user requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY --chown=user . .

# Hugging Face Spaces exposes port 7860 by default
EXPOSE 7860

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
