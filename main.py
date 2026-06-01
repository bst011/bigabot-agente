from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import google.generativeai as genai
import os
import traceback
import urllib.request
import urllib.parse
import json
from pdf_generator import crear_pdf_prospeccion

app = FastAPI()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio. Modo Radar Estricto."}

@app.get("/investigar/{nicho}")
async def investigar_clientes(nicho: str):
    try:
        # --- RADAR ESTRICTO DE GOOGLE MAPS ---
        nombres_reales = ""
        
        if not MAPS_API_KEY:
            return JSONResponse(content={"alerta": "La variable GOOGLE_MAPS_API_KEY no existe en Render."})
            
        try:
            query_codificada = urllib.parse.quote(nicho)
            url_maps = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query_codificada}&key={MAPS_API_KEY}"
            
            respuesta_maps = urllib.request.urlopen(url_maps)
            datos_maps = json.loads(respuesta_maps.read())
            
            if datos_maps.get('status') != 'OK':
                return JSONResponse(content={
                    "alerta": "Google Maps bloqueó la búsqueda.",
                    "status": datos_maps.get('status'),
                    "detalles": datos_maps.get('error_message', 'Sin detalles adicionales. Revisa las restricciones de tu API Key.')
                })
                
            resultados = datos_maps.get('results', [])[:3]
            
            if not resultados:
                return JSONResponse(content={"alerta": f"Google Maps no encontró ningún negocio real para: {nicho}"})
                
            for lugar in resultados:
                direccion = lugar.get('formatted_address', 'Dirección no especificada')
                nombres_reales += f"- {lugar['name']} (Ubicación: {direccion})\n"
                
        except Exception as e_maps:
            return JSONResponse(content={"alerta": "Falla de conexión con Google Maps.", "error_tecnico": str(e_maps)})
        # ------------------------------------

        nombre_modelo = 'gemini-1.0-pro'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nombre_modelo = m.name
                break
                
        model = genai.GenerativeModel(nombre_modelo)
        
        prompt = f"""
        Actúa como Director de Crecimiento de la agencia BigaEstudio.
        Hemos extraído de Google Maps los siguientes negocios reales:
        
        {nombres_reales}
        
        Crea una estrategia de prospección para ESTOS negocios específicamente.
        Para cada uno detalla:
        - Nombre REAL del negocio y su ubicación.
        - El principal error o debilidad estratégica que suelen tener los negocios de este tipo en su identidad visual.
        - Cómo BigaEstudio resolverá este problema con un manual estructurado.
        REGLA ESTRICTA: Cíñete a los nombres proporcionados. NO uses formato Markdown. NO uses asteriscos (*). NO uses numerales (#). NO uses guiones largos. Escribe SOLO en texto plano tradicional.
        """
        
        respuesta = model.generate_content(prompt)
        texto_ia = respuesta.text.encode('latin-1', 'ignore').decode('latin-1')
        
        try:
            nombre_archivo = "Reporte_Prospectos.pdf"
            crear_pdf_prospeccion(texto_ia, nombre_archivo)
            return FileResponse(nombre_archivo, media_type='application/pdf', filename=f"Prospeccion_Maps.pdf")
            
        except Exception as error_pdf:
            return JSONResponse(content={"alerta": "Falla en PDF", "reporte": texto_ia})

    except Exception as error_ia:
        return JSONResponse(content={"alerta": "Error de Gemini", "detalles": traceback.format_exc()})