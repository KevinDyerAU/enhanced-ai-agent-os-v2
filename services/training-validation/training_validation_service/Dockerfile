FROM python:3.12-slim

# Install system dependencies required for unstructured library
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only=main --no-root

# Pre-download NLTK packages to avoid HTTP 403 errors during runtime
RUN python -c "import nltk; nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger_eng', quiet=True)"

COPY . .

EXPOSE 8033

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8033"]
