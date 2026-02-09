FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev pkg-config gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY clients.py .

CMD ["python", "-m", "uvicorn", "clients:app", "--host", "0.0.0.0", "--port", "8001"]