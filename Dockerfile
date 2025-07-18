FROM python:3.13-alpine

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# 1) 빌드용(.build-deps) 및 런타임용 의존성 설치
# 2) Poetry & export 플러그인 설치
RUN apk add --no-cache --virtual .build-deps \
        build-base \
        libffi-dev \
        openssl-dev \
        leptonica-dev \
        tesseract-ocr-dev \
    && apk add --no-cache \
        tesseract-ocr \
        tesseract-ocr-data-eng \
    && pip install --no-cache-dir poetry poetry-plugin-export

# 3) 의존성 정의 파일 복사
COPY pyproject.toml poetry.lock README.md ./

# 4) requirements.txt로 내보내고 설치한 뒤 빌드 의존성 제거
RUN poetry export -f requirements.txt --output requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt \
    && apk del .build-deps

# 5) 애플리케이션 소스 복사
COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
