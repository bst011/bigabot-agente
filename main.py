from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import google.generativeai as genai
import os
import traceback
from pdf_generator import crear_pdf_prospeccion

app = FastAPI()

# Conecta con la llave secreta que guardamos de Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio Activo. BigaBot en Modo IA Nativa."}

@app.get("/investigar/{nicho}")
async def investigar_clientes(nicho: str):
    try:
        # Le preguntamos a Google qué cerebro tenemos autorizado usar
        nombre_modelo = 'gemini-1.0-pro'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nombre_modelo = m.name
                break
                
        model = genai.GenerativeModel(nombre_modelo)
        
        # El Prompt exige negocios reales desde el conocimiento de la IA
        prompt = f"""
        Actúa como Director de Crecimiento de la agencia BigaEstudio.
        Investiga el siguiente nicho: {nicho}.
        Busca en tu base de datos y selecciona 3 negocios REALES, VERDADEROS y EXISTENTES en esa ubicación o rubro. 
        Para cada uno detalla:
        - Nombre real del negocio y su ubicación aproximada.
        - El principal error o debilidad estratégica en su identidad visual o branding actual.
        - Cómo BigaEstudio resolverá este problema con un manual estructurado.
        REGLA ESTRICTA: Los negocios DEBEN existir en la vida real. NO inventes nombres. NO uses formato Markdown. NO uses asteriscos (*). NO uses numerales (#). NO uses guiones largos. Escribe SOLO en texto plano tradicional.
        """
        
        # El agente piensa y genera el contenido
        respuesta = model.generate_content(prompt)
        
        # Filtro definitivo para evitar que el PDF colapse con símbolos raros
        texto_ia = respuesta.text.encode('latin-1', 'ignore').decode('latin-1')
        
        try:
            # Intentamos enviar el texto a la imprenta PDF
            nombre_archivo = "Reporte_Prospectos.pdf"
            crear_pdf_prospeccion(texto_ia, nombre_archivo)
            
            # Si funciona, descarga el PDF directamente
            return FileResponse(nombre_archivo, media_type='application/pdf', filename=f"Prospeccion_Nativa.pdf")
            
        except Exception as error_pdf:
            return JSONResponse(content={
                "alerta": "El texto se generó con éxito, pero la imprenta PDF falló.",
                "reporte_generado": texto_ia
            })

    except Exception as error_ia:
        return JSONResponse(content={
            "alerta": "Error de conexión con el cerebro de Gemini.",
            "error_tecnico": str(error_ia),
            "detalles": traceback.format_exc()
        })