FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY feed.py /app/feed.py
COPY ingest_text_files.py /app/ingest_text_files.py
COPY app.py /app/app.py

EXPOSE 8000

RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 tesseract-ocr graphviz \
    && rm -rf /var/lib/apt/lists/*

CMD ["uvicorn", "feed:app", "--host", "0.0.0.0", "--port", "8000"]