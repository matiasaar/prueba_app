import os
import time
import shutil
import mlflow
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage  # Nueva librería para el Bucket

# --- CONFIGURACIÓN INICIAL ---
app = FastAPI(title="Gemini Dog Scanner MLOps Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Google Cloud Storage
BUCKET_NAME = "dog-scanner-ml-data"
storage_client = storage.Client()

def upload_to_bucket(file_path, destination_blob_name):
    """Sube un archivo al bucket de Google Cloud."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    return f"gs://{BUCKET_NAME}/{destination_blob_name}"

# Configura Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

# CONFIGURACIÓN MLOPS: MLflow con GCS
# Esto hace que los videos y resultados se guarden en el bucket
mlflow.set_experiment("Dog_Analysis_v1")
artifact_uri = f"gs://{BUCKET_NAME}/mlflow-artifacts"

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "online", "model": "gemini-2.5-flash", "bucket": BUCKET_NAME}

@app.post("/analyze-dog")
async def analyze_video(file: UploadFile = File(...)):
    # Iniciamos el run de MLflow
    with mlflow.start_run(run_name=f"scan_{file.filename}"):
        start_time = time.time()
        # Nombre único para el archivo temporal y el bucket
        timestamp = int(time.time())
        temp_path = f"temp_{timestamp}_{file.filename}"
        gcs_blob_name = f"videos/{timestamp}_{file.filename}"

        try:
            # 1. Guardar video localmente temporalmente
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 2. FASE 2.5: Subir al Bucket de Google Cloud (Persistencia)
            gcs_url = upload_to_bucket(temp_path, gcs_blob_name)
            mlflow.log_param("gcs_video_path", gcs_url)
            
            # 3. Subida a Gemini API
            video_file = genai.upload_file(path=temp_path)
            
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise Exception("Gemini Video Processing Failed")

            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = """
            Eres un experto en comportamiento canino. Analiza el video y extrae:
            1. RAZA: Identifica la raza.
            2. DESCRIPCIÓN: Acción física (max 5 palabras).
            3. INSTRUCCIÓN: Orden detectada y si el perro cumple.

            FORMATO JSON:
            {"raza": "...", "descripcion": "...", "orden_detectada": "...", "cumple_orden": "si/no"}
            """

            response = model.generate_content([video_file, prompt])
            
            # 4. Registro de Métricas y Artefactos en MLflow
            duration = time.time() - start_time
            mlflow.log_metric("inference_time_sec", duration)
            
            # Guardamos la respuesta de la IA como un archivo en MLflow (que irá al Bucket)
            with open("response.json", "w") as f:
                f.write(response.text)
            mlflow.log_artifact("response.json")

            return {
                "success": True,
                "analysis": response.text,
                "video_cloud_url": gcs_url,
                "metadata": {"duration_sec": round(duration, 2)}
            }

        except Exception as e:
            mlflow.log_param("status", "failed")
            mlflow.log_error(str(e))
            raise HTTPException(status_code=500, detail=str(e))
        
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    # Importante: Cloud Run usa la variable PORT, si no existe usa 8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)