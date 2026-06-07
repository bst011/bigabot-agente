import os
import json
import requests
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from pdf_generator import crear_pdf_prospeccion
from bs4 import BeautifulSoup
import re

# 1. Inicialización de la App
app = FastAPI()

# --- 🧠 EL CEREBRO DE MEMORIA ---
memoria_usuarios = {}

# 3. Rutas Básicas
@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio activo. Motor de prospección en línea..."}

@app.get("/descargar-pdf")
def entregar_pdf():
    return FileResponse(
        "Reporte_BigaEstudio.pdf", 
        media_type='application/pdf', 
        filename="Prospeccion_BigaEstudio.pdf"
    )

# 4. Herramientas de Prospección
def buscar_negocios_locales(query, api_key):
    try:
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.websiteUri,places.nationalPhoneNumber,places.rating,places.userRatingCount,places.formattedAddress,places.reviews,places.googleMapsUri"
        }
        data = {"textQuery": query}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json().get('places', [])
        else:
            return []
    except Exception as e:
        print(f"Error en buscar_negocios_locales: {e}")
        return []

def francotirador_web(url):
    if not url or url == 'No tiene página web oficial':
        return "Ausencia total de ecosistema web."
    try:
        # Timeout bajado a 2 para soportar múltiples webs sin romper el límite de WhatsApp
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=2)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        links = soup.find_all('a', href=True)
        rrss = set()
        emails = set()
        for a in links:
            href = a.get('href', '').lower()
            if 'instagram.com' in href: rrss.add('Instagram')
            if 'facebook.com' in href: rrss.add('Facebook')
            if 'tiktok.com' in href: rrss.add('TikTok')
            if 'mailto:' in href: emails.add(href.replace('mailto:', ''))
        
        correos_texto = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', soup.text)
        emails.update(correos_texto)
        
        estado = f"Puntos de contacto detectados: {', '.join(rrss) if rrss else 'Sin integración social'}. "
        estado += f"Líneas de correo: {', '.join(emails) if emails else 'Inexistentes (Fricción de contacto alta)'}."
        return estado
    except:
        return "Servidor inestable o web caída. Grave falla de infraestructura digital."


# 5. Ruta Principal de WhatsApp Webhook
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        mensaje_usuario = form_data.get('Body', '').lower()
        remitente = form_data.get('From', '')
        
        # Conexión a las APIs
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        google_api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
        
        instrucciones_sistema = "Eres BigaBot, estratega principal de adquisición B2B de BigaEstudio."

        # MODO 1: INVESTIGACIÓN DINÁMICA
        if "investig" in mensaje_usuario or "reporte" in mensaje_usuario:
            
            query_busqueda = mensaje_usuario.replace("investiga", "").replace("reporte", "").replace("de", "").strip()
            if not query_busqueda:
                query_busqueda = "negocios locales"
                
            resultados_maps = buscar_negocios_locales(query_busqueda, google_api_key)
            
            if resultados_maps:
                info_lugares = "DATA CRUDA DE LOS OBJETIVOS (TOP 3 DEL RUBRO):\n\n"
                
                # Tomamos hasta los 3 primeros resultados
                for indice, p in enumerate(resultados_maps[:3]):
                    nombre = p.get('displayName', {}).get('text', 'Sin nombre')
                    web = p.get('websiteUri', 'No tiene página web oficial')
                    tel = p.get('nationalPhoneNumber', 'No tiene teléfono público')
                    direccion = p.get('formattedAddress', 'Dirección no especificada')
                    rating = p.get('rating', 'Sin calificación')
                    reviews = p.get('userRatingCount', '0')
                    
                    datos_scrap = francotirador_web(web)
                    
                    info_lugares += f"PROSPECTO {indice + 1}:\n"
                    info_lugares += f"- Entidad: {nombre}\n- Base Operativa: {direccion}\n- Infraestructura Web: {web}\n- Canal Telefónico: {tel}\n- Reputación: {rating} estrellas (Volumen: {reviews} reseñas)\n"
                    info_lugares += f"- Diagnóstico de Nodos Web: {datos_scrap}\n"
                    info_lugares += "--------------------------------------------------\n"
            else:
                info_lugares = "El radar no encontró entidades exactas en Maps para esta consulta."

            # EL NUEVO CEREBRO: PROSPECTOS MÚLTIPLES
            instrucciones_sistema = """Eres BigaBot, Arquitecto de Soluciones Digitales. Auditas nichos de mercado en Chile para estructurar su digitalización.

REGLAS ESTRICTAS DE ANÁLISIS:
1. CONTEXTO GEOGRÁFICO: Si la dirección indica una comuna metropolitana o de alto tráfico, sugiere automatización pesada. Si es una zona más rural o comunitaria, sugiere herramientas ágiles (ej. WhatsApp Business, perfiles de Google locales) antes que un e-commerce complejo.
2. PROYECCIÓN FINANCIERA REALISTA: NO uses números fijos. Calcula la estimación de fuga de capital basándote proporcionalmente en el volumen de reseñas y el ticket promedio del rubro analizado.

ESTRUCTURA EXACTA DE TU RESPUESTA:

[REPORTE CLIENTE]
Redacta 3 párrafos como consultor estratégico analizando el mercado local:
Párrafo 1: Visión General del Rubro. Menciona los negocios analizados y destaca el patrón de fallas o aciertos digitales que encontraste entre ellos (quién lidera, quién se queda atrás).
Párrafo 2: El Foco de Oportunidad. Elige al prospecto que tenga más potencial de mejora (el que pierde más dinero por su fricción actual) y calcula su fuga de capital mensual en CLP de forma lógica.
Párrafo 3: Puente Estratégico. Propuesta de sesión de 10 minutos dirigida a ese negocio específico o al rubro en general para ensamblar una solución definitiva.
Usa <b>texto</b> para resaltar datos duros.

[PLAN INTERNO]
Instrucciones de arquitectura para el equipo de desarrollo.
- 📐 Estructura Sugerida: [Software o plataforma viable según el entorno geográfico y tamaño del nicho].
- 🔌 Nodos de Integración: [Cómo conectar la solución sin interrumpir su operación física actual].
- 🎯 Eje de Conversión: [El punto de dolor específico a presionar durante la reunión comercial].
"""

            prompt_auditoria = f"Ejecuta el análisis de mercado sobre la siguiente estructura comercial:\n{info_lugares}\n\nGenera el reporte de nicho para el cliente y el esquema interno."
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": instrucciones_sistema},
                    {"role": "user", "content": prompt_auditoria}
                ],
               model="llama-3.3-70b-versatile",
               temperature=0.4
            )

            respuesta_completa = chat_completion.choices[0].message.content
            
            if "[PLAN INTERNO]" in respuesta_completa:
                partes = respuesta_completa.split("[PLAN INTERNO]")
                texto_pdf = partes[0].replace("[REPORTE CLIENTE]", "").strip()
                plan_interno = "Arquitectura Técnica Recomendada:\n\n" + partes[1].strip()
            else:
                texto_pdf = respuesta_completa
                plan_interno = "Error de parseo: La IA no dividió los bloques. Revisa el PDF."

            crear_pdf_prospeccion(texto_pdf, "Reporte_BigaEstudio.pdf", "logo.png")
            
            url_pdf = "https://bigabot-agente.onrender.com/descargar-pdf"
            texto_chat = f"¡Diagnóstico de terreno completado! 🚀\n\n{plan_interno}"
            
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
                memoria_usuarios[remitente] = [
                    {"role": "system", "content": instrucciones_sistema}
                ]
            
            memoria_usuarios[remitente].append({"role": "user", "content": mensaje_usuario})
            
            chat_completion = client.chat.completions.create(
                messages=memoria_usuarios[remitente],
                model="llama-3.1-8b-instant",
            )
            
            respuesta_ia = chat_completion.choices[0].message.content
            memoria_usuarios[remitente].append({"role": "assistant", "content": respuesta_ia})
            
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Message><Body>{respuesta_ia}</Body></Message>
            </Response>"""
            return Response(content=xml_response, media_type="application/xml")

    except Exception as e:
        print(f"Error técnico en el webhook: {e}")
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message><Body>Ajustando conexiones en la base de datos. Dame un minuto y repite la orden.</Body></Message>
        </Response>"""
        return Response(content=error_xml, media_type="application/xml")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)