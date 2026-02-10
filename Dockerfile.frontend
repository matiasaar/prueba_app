FROM python:3.11-slim

# Evita que Python genere archivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir streamlit requests

# Copiamos el código de la web app
COPY app.py .

# Streamlit usa el puerto 8501 por defecto, pero Cloud Run usa el 8080
EXPOSE 8080

# Comando para ejecutar streamlit en el puerto que pide Cloud Run
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]