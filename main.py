from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import google.generativeai as genai
import os
import traceback
from pdf_generator import crear_pdf_prospeccion

app = FastAPI()

# Conecta con la llave secreta que guardamos
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio Activo. BigaBot esperando ordenes."}

@app.get("/investigar/{nicho}")
async def investigar_clientes(nicho: str):
    try:
        # 1. Le preguntamos a Google qué cerebro tenemos autorizado usar
        nombre_modelo = 'gemini-1.0-pro' # Respaldo por defecto
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nombre_modelo = m.name
                break
                
        # 2. Usamos exactamente el modelo que Google nos entregó
        model = genai.GenerativeModel(nombre_modelo)
        
        prompt = f"""
        Actúa como Director de Crecimiento de la agencia BigaEstudio.
        Investiga el siguiente nicho: {nicho}.
        Crea 3 perfiles de clientes potenciales ficticios pero altamente realistas.
        Para cada uno detalla:
        - Nombre del negocio.
        - El principal error en su identidad visual o branding actual.
        - Cómo BigaEstudio resolverá este problema con un manual estructurado.
        REGLA ESTRICTA: NO uses formato Markdown. NO uses asteriscos (*). NO uses numerales (#). NO uses guiones largos. Escribe SOLO en texto plano tradicional como un bloc de notas.
        """
        
        # El agente piensa y genera el contenido
        respuesta = model.generate_content(prompt)
        
        # Filtro definitivo: Aplana cualquier símbolo extraño a texto básico para que la imprenta PDF no colapse
        texto_ia = respuesta.text.encode('latin-1', 'ignore').decode('latin-1')
        
        try:
            # Intentamos enviar el texto a la imprenta PDF
            nombre_archivo = "Reporte_Prospectos.pdf"
            crear_pdf_prospeccion(texto_ia, nombre_archivo)
            
            # Si funciona, descarga el PDF directamente
            return FileResponse(nombre_archivo, media_type='application/pdf', filename=f"Prospeccion_{nicho}.pdf")
            
        except Exception as error_pdf:
            # Si la imprenta falla, mostramos el texto en pantalla para no perderlo
            return JSONResponse(content={
                "alerta": "La IA escribió el reporte, pero el creador de PDF falló.",
                "error_tecnico": str(error_pdf),
                "reporte_generado": texto_ia
            })

    except Exception as error_ia:
        # Si Gemini falla, mostramos el error exacto
        return JSONResponse(content={
            "alerta": "Error de conexión con el cerebro de Gemini.",
            "error_tecnico": str(error_ia),
            "modelo_intentado": nombre_modelo,
            "detalles": traceback.format_exc()
        })