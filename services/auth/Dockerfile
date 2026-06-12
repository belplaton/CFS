FROM python:3.11-slim

RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app

USER app

# Apply Alembic migrations, then start the service.  Both steps are
# explicit so they show up in container logs and can be reasoned about
# independently during incident response.
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
