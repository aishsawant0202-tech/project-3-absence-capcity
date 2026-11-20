FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Migrations, so the container can create the tables in a new (empty) database
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

# First bring the database up to date (creates the tables on the first start), then start the API
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
