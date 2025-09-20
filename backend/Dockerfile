FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copia mínima; en desarrollo el volumen override monta todo backend
COPY app ./app
EXPOSE 5555
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5555"]
