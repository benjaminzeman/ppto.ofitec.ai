FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install --no-cache-dir -r requirements.txt
# Copia mínima; en desarrollo el volumen override monta todo backend
COPY app ./app
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 5555
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5555"]
