FROM python:3.13-slim

WORKDIR /app

RUN pip install poetry poetry-plugin-export
COPY pyproject.toml poetry.lock README.md ./
RUN poetry export -f requirements.txt --output requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libtesseract-dev libleptonica-dev \
      tesseract-ocr \
      tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8001
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
