from fastapi import FastAPI
from fastapi.responses import FileResponse
import google.generativeai as genai
import os
from pdf_generator import crear_pdf_prospeccion

app = FastAPI()

# Conecta con la llave secreta que guardamos
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio Activo. BigaBot esperando ordenes."}

@app.get("/investigar/{nicho}")
async def investigar_clientes(nicho: str):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Actúa como Director de Crecimiento de la agencia BigaEstudio.
    Investiga el siguiente nicho: {nicho}.
    Crea 3 perfiles de clientes potenciales ficticios pero altamente realistas.
    Para cada uno detalla:
    - Nombre del negocio.
    - El principal error en su identidad visual o branding actual.
    - Cómo BigaEstudio resolverá este problema con un manual estructurado.
    REGLA ESTRICTA: NO uses absolutamente NINGUN emoji, ícono, ni símbolos especiales. Utiliza SOLO texto plano tradicional. Usa formato Markdown limpio. Usa '##' para títulos de cada cliente.
    """
    
    # El agente piensa y genera el contenido
    respuesta = model.generate_content(prompt)
    texto_ia = respuesta.text
    
    # Enviamos el texto a la imprenta PDF
    nombre_archivo = "Reporte_Prospectos.pdf"
    crear_pdf_prospeccion(texto_ia, nombre_archivo)
    
    # Devuelve el PDF directamente a tu celular
    return FileResponse(nombre_archivo, media_type='application/pdf', filename=f"Prospeccion_{nicho}.pdf")
