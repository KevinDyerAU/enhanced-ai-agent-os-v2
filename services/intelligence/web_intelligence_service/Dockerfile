FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only=main --no-root

COPY . .

EXPOSE 8032

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8032"]
