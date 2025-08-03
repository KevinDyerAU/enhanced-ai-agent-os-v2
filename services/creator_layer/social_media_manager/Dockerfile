FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only=main --no-root

COPY . .

EXPOSE 8004

CMD ["poetry", "run", "uvicorn", "social_media_manager.main:app", "--host", "0.0.0.0", "--port", "8004"]
