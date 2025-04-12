# Stage 1: Build environment
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies (if any, e.g., for compiling packages)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Copy requirements file
COPY requirements.txt .

# Install dependencies into a virtual environment within the builder stage
# This avoids polluting the final image with build tools
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app

# Stage 2: Production environment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code (specifically the app directory)
COPY --from=builder /app/app /app/app

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable for the Python path
ENV PYTHONPATH=/app

# Activate the virtual environment and run the application
ENV PATH="/opt/venv/bin:$PATH"

# Command to run the application using Uvicorn
# Use 0.0.0.0 to bind to all network interfaces within the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 