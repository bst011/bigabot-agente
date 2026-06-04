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
        
        # Configuración del Agente IA
        instrucciones_base = """
        Eres BigaBot, estratega principal de adquisición y auditoría B2B de la agencia BigaEstudio. Tu objetivo es analizar negocios locales y detectar oportunidades urgentes de digitalización o automatización. Me enviarás los reportes directamente por WhatsApp.
        
        REGLAS:
        1. Evalúa fricción: ¿Tienen web? ¿Tienen enlace directo a WhatsApp? Si no lo tienen, es una falla crítica en su sistema de ventas.
        2. Estructura estricta: Tu respuesta DEBE contener solo 3 cosas: Nombre del Negocio, Diagnóstico (el problema detectado) y Ángulo de Venta Recomendado (ej: Bot de WhatsApp o Ecosistema Web).
        3. Formato para WhatsApp: NO uses asteriscos ni negritas de Markdown bajo ninguna circunstancia. Usa texto plano, guiones para listar y un par de emojis para separar la información.
        4. Sé ultra directo, sin saludos largos. Máximo 3 párrafos cortos.
        """
        
        # 1. Usamos el modelo más estable y universal
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
            
            texto_chat = "¡Circuito completado! Aquí tienes tu reporte. ¿Sobre qué otro tema te gustaría que investiguemos?"
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
            
        # MODO 2: CHAT CONTINUO CON MEMORIA
        else:
            if remitente not in memoria_usuarios:
                # 2. El truco: Le inyectamos su personalidad directamente como su primer recuerdo
                memoria_usuarios[remitente] = [
                    {"role": "user", "parts": [instrucciones_base]},
                    {"role": "model", "parts": ["Entendido. Soy BigaBot y estoy listo para auditar negocios."]}
                ]
                
            chat = model.start_chat(history=memoria_usuarios[remitente])
            respuesta_ia = chat.send_message(mensaje_usuario)
            memoria_usuarios[remitente] = chat.history
            
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Message>
                    <Body>{respuesta_ia.text}</Body>
                </Message>
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