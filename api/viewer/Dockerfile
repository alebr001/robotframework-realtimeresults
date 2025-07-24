FROM python:3.11-slim

WORKDIR /app

COPY ./main.py .
COPY ./__init__.py .
COPY ../../shared ./shared

RUN pip install --no-cache-dir fastapi uvicorn[standard] psycopg2-binary

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
