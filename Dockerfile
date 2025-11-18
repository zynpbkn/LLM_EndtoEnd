FROM python:3.12-slim

# Optional but useful for logs
ENV PYTHONUNBUFFERED=1

# Set workdir early
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY feed.py /app/feed.py
COPY ingest_text_files.py /app/ingest_text_files.py
COPY app.py /app/app.py

# (Optional) tell which port the container listens on
EXPOSE 8000

# Run the app with uvicorn
CMD ["uvicorn", "feed:app", "--host", "0.0.0.0", "--port", "8000"]