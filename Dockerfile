FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UOA_HOST=0.0.0.0

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY ui /app/ui
COPY demo /app/demo

RUN pip install --upgrade pip && pip install .

EXPOSE 8000

CMD ["python3", "-m", "uoa_agent"]
