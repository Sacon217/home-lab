FROM python:3.15-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY email_parser.py .
COPY fast_api.py .

EXPOSE 8000

CMD ["uvicorn", "fast_api:app", "--host", "0.0.0.0", "--port", "8000"]