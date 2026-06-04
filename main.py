import os
import json
import requests
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
import google.generativeai as genai
from pdf_generator import crear_pdf_prospeccion

# 1. Inicialización de la App
app = FastAPI()

# 2. Configuración de Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# --- 🧠 EL CEREBRO DE MEMORIA ---
memoria_usuarios = {}

# 3. Rutas Básicas
@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio. Escuchando WhatsApp con memoria..."}

@app.get("/descargar-pdf")
def entregar_pdf():
    return FileResponse(
        "Reporte_BigaEstudio.pdf", 
        media_type='application/pdf', 
        filename="Prospeccion_BigaEstudio.pdf"
    )

# 4. Herramienta de Prospección (API Google Places)
def buscar_negocios_locales(query_usuario, api_key):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-ApiKey": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,places.rating,places.userRatingCount"
    }
    payload = {
        "textQuery": query_usuario,
        "languageCode": "es"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("places", [])
        else:
            print(f"Error en la API de Google: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error de conexión: {e}")
        return []

# 5. Ruta Principal de WhatsApp Webhook
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        mensaje_usuario = form_data.get('Body', '').lower()
        remitente = form_data.get('From', '')
        
        # 1. Usamos gemini-pro (El modelo más estable y universal)
        model = genai.GenerativeModel('gemini-pro')
        
        # MODO 1: EL CLIENTE PIDE UNA INVESTIGACIÓN
        if "investig" in mensaje_usuario or "reporte" in mensaje_usuario or "pdf" in mensaje_usuario:
            texto_pdf = """
            BigaEstudio | Reporte de Prueba Técnica
            Negocio 1: Ferretería de Prueba
            Error visual actual: Letrero sin identidad.
            Solución BigaEstudio: Manual de marca.
            """
            crear_pdf_prospeccion(texto_pdf, "Reporte_BigaEstudio.pdf")
            texto_chat = "¡Circuito completado! Aquí tienes tu reporte."
            url_pdf = "https://bigabot-agente.onrender.com/descargar-pdf"
            
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Message>
                    <Body>{texto_chat}</Body>
                    <Media>{url_pdf}</Media>
                </Message>
            </Response>"""
            
            if remitente in memoria_usuarios:
                del memoria_usuarios[remitente]
            return Response(content=xml_response, media_type="application/xml")
            
        # MODO 2: CHAT CONTINUO
        else:
            if remitente not in memoria_usuarios:
                # 2. El Truco Maestro: Le damos sus reglas como el "historial" inicial
                memoria_usuarios[remitente] = [
                    {"role": "user", "parts": ["INSTRUCCIONES SECRETAS: Actúa como BigaBot, estratega principal de adquisición B2B de BigaEstudio. Analiza negocios locales y detecta oportunidades urgentes. REGLAS: 1. Evalúa si tienen web o WhatsApp. 2. Tu respuesta DEBE contener: Nombre del Negocio, Diagnóstico y Ángulo de Venta. 3. NO uses Markdown (ni negritas ni asteriscos). 4. Sé ultra directo. Responde 'Entendido' para confirmar."]},
                    {"role": "model", "parts": ["Entendido. Soy BigaBot y estoy listo para auditar."]}
                ]
                
            chat = model.start_chat(history=memoria_usuarios[remitente])
            respuesta_ia = chat.send_message(mensaje_usuario)
            memoria_usuarios[remitente] = chat.history
            
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Message><Body>{respuesta_ia.text}</Body></Message>
            </Response>"""
            return Response(content=xml_response, media_type="application/xml")

    except Exception as e:
        print(f"Error técnico en el webhook: {e}")
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message><Body>Dame un segundo que estoy procesando demasiada información. Volvamos a intentarlo.</Body></Message>
        </Response>"""
        return Response(content=error_xml, media_type="application/xml")


# 6. Arranque del Servidor (El motor que le faltaba a Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)