FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS dev
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod
COPY . .
# /app/uploads existe dans l'image et appartient à `app` : un volume nommé monté dessus en hérite.
RUN useradd --system app && mkdir -p /app/uploads && chown -R app /app
USER app
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
