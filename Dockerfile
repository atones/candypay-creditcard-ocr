FROM python:3.13-slim

RUN pip install --no-cache-dir poetry

WORKDIR /code
COPY pyproject.toml poetry.lock README.md ./

RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

COPY . .

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
