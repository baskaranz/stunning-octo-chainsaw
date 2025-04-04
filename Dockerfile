FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the application
RUN pip install --no-cache-dir -e .

# Expose the application port
EXPOSE 8000

# Use a non-root user for security
RUN useradd -m appuser
USER appuser

# Run the application
CMD ["python", "main.py"]