import streamlit as st
import requests

st.set_page_config(page_title="Dog Scanner AI", page_icon="🐶")

# Estilo Dark Mode Pro con CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { 
        background: linear-gradient(to right, #007cf0, #00dfd8); 
        color: white; border: none; border-radius: 10px; height: 3em; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🐶 Dog Scanner AI")
st.write("Toma una foto de tu perro y Gemini te dirá qué está haciendo.")

# Componente de Cámara
img_file = st.camera_input("Escanea a tu perro")

if img_file:
    st.image(img_file, caption="Foto capturada", use_column_width=True)
    
    with st.spinner("Gemini está analizando..."):
        # Enviamos la imagen a tu backend de Cloud Run
        files = {"file": img_file.getvalue()}
        # REEMPLAZA CON TU URL DE CLOUD RUN
        URL = "https://dog-scanner-backend-XXXXX.a.run.app/analyze-dog" 
        
        try:
            response = requests.post(URL, files=files)
            result = response.json()
            
            st.success("¡Análisis completo!")
            st.subheader(f"Raza: {result['breed']}")
            st.info(f"Descripción: {result['description']}")
        except Exception as e:
            st.error(f"Error conectando con el servidor: {e}")