FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get install libpq-dev
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
