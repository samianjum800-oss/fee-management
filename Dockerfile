FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies (for psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build the user manual that Django serves under /help/.
RUN python -m mkdocs build --strict

# Create persistent directories
RUN mkdir -p /data/staticfiles /data/media
ENV DATABASE_URL=postgresql://dummy:dummy@localhost:5432/dummy

# Collect static files (shared schema)
RUN python manage.py collectstatic --noinput

# Copy entrypoint script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 7860

CMD ["/start.sh"]
