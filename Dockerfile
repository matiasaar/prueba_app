# Usa una imagen ligera de Python
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependencias del sistema necesarias para procesamiento de video
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 && apt-get clean

# Instalar dependencias de Python
COPY requirements.txt .
RUN  pip install --no-cache-dir --upgrade pip && \
     pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY . .

# Variable para que MLflow sepa dónde escribir en la nube
ENV MLFLOW_TRACKING_URI=sqlite:///mlflow.db


# Comando para ejecutar la app (Uvicorn) usando la variable $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]


# # Exponer el puerto de FastAPI
# EXPOSE 8000
# # Comando para ejecutar la app (Uvicorn)
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
