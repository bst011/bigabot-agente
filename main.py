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

# Conecta con las llaves secretas
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio Activo con radar Maps. BigaBot esperando ordenes."}

@app.get("/investigar/{nicho}")
async def investigar_clientes(nicho: str):
    try:
        # --- NUEVO: RADAR DE GOOGLE MAPS ---
        nombres_reales = ""
        try:
            if MAPS_API_KEY:
                # Codificamos la búsqueda (ej: panaderias en temuco -> panaderias%20en%20temuco)
                query_codificada = urllib.parse.quote(nicho)
                url_maps = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query_codificada}&key={MAPS_API_KEY}"
                
                respuesta_maps = urllib.request.urlopen(url_maps)
                datos_maps = json.loads(respuesta_maps.read())
                resultados = datos_maps.get('results', [])[:3] # Tomamos los 3 primeros
                
                for lugar in resultados:
                    direccion = lugar.get('formatted_address', 'Dirección no especificada')
                    nombres_reales += f"- {lugar['name']} (Ubicación: {direccion})\n"
        except Exception as e_maps:
            print(f"Error en Maps: {e_maps}")
            
        # Si por alguna razón Maps falla, tenemos un texto de respaldo
        if not nombres_reales:
            nombres_reales = "Busca en tu base de datos 3 negocios reales e icónicos que coincidan con la búsqueda."
        # ------------------------------------

        # Le preguntamos a Google qué cerebro de IA tenemos autorizado usar
        nombre_modelo = 'gemini-1.0-pro'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nombre_modelo = m.name
                break
                
        model = genai.GenerativeModel(nombre_modelo)
        
        # El Prompt ahora inyecta los negocios reales del mapa
        prompt = f"""
        Actúa como Director de Crecimiento de la agencia BigaEstudio.
        Hemos extraído de Google Maps los siguientes negocios reales para el nicho '{nicho}':
        
        {nombres_reales}
        
        Tu tarea es crear una estrategia de prospección para ESTOS negocios específicamente.
        Para cada uno detalla:
        - Nombre REAL del negocio y su ubicación.
        - El principal error o debilidad estratégica que suelen tener los negocios de este tipo en su identidad visual.
        - Cómo BigaEstudio resolverá este problema con un manual estructurado y una propuesta de valor.
        REGLA ESTRICTA: Cíñete a los nombres proporcionados. NO uses formato Markdown. NO uses asteriscos (*). NO uses numerales (#). NO uses guiones largos. Escribe SOLO en texto plano tradicional.
        """
        
        respuesta = model.generate_content(prompt)
        
        # Filtro definitivo para evitar que el PDF colapse con símbolos raros
        texto_ia = respuesta.text.encode('latin-1', 'ignore').decode('latin-1')
        
        try:
            nombre_archivo = "Reporte_Prospectos.pdf"
            crear_pdf_prospeccion(texto_ia, nombre_archivo)
            return FileResponse(nombre_archivo, media_type='application/pdf', filename=f"Prospeccion_Maps.pdf")
            
        except Exception as error_pdf:
            return JSONResponse(content={
                "alerta": "El texto se generó con éxito, pero la imprenta PDF falló.",
                "negocios_encontrados": nombres_reales,
                "reporte_generado": texto_ia
            })

    except Exception as error_ia:
        return JSONResponse(content={
            "alerta": "Error de conexión con el cerebro de Gemini.",
            "error_tecnico": str(error_ia),
            "detalles": traceback.format_exc()
        })