FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS dev
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod
COPY . .
RUN useradd --system app && chown -R app /app
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
