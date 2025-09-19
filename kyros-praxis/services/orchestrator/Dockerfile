FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Set PYTHONPATH to include the app directory and make it a package
ENV PYTHONPATH=/app
RUN touch /app/__init__.py

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]