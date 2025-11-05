FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/srv/app

# Системные зависимости для OCR/ASR/изображений/сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng \
    build-essential cmake git curl ca-certificates \
    libmagic1 libgomp1 \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 \
    libjpeg62-turbo-dev zlib1g-dev libpng-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/app

# Установка Python-зависимостей
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Копируем исходники
COPY . .

EXPOSE 8000
CMD ["uvicorn","app.api.main:app","--host","0.0.0.0","--port","8000"]
