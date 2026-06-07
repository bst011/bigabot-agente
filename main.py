import os
import json
import requests
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from pdf_generator import crear_pdf_prospeccion

# 1. Inicialización de la App
app = FastAPI()

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
import requests
from bs4 import BeautifulSoup
import re

def buscar_negocios_locales(query, api_key):
    try:
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            # Ahora pedimos reseñas y links de Google Maps también
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
        return "No tiene web para espiar."
    try:
        # Timeout de 3 segundos para que WhatsApp no corte la llamada
        res = requests.get(url, timeout=3)
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
        
        estado = f"Redes conectadas en su web: {', '.join(rrss) if rrss else '¡Ninguna! (Punto ciego)'}. "
        estado += f"Correos visibles: {', '.join(emails) if emails else 'Ninguno (Difícil contacto)'}."
        return estado
    except:
        return "Su página web está caída, da error o tarda mucho en cargar (¡Grave problema de servidor!)."


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
        google_api_key = os.environ.get("GOOGLE_PLACES_API_KEY") # Nueva llave requerida
        
        # PERSONALIDAD DEL AGENTE
        instrucciones_sistema = "Eres BigaBot, estratega principal de adquisición B2B de BigaEstudio."

        # MODO 1: EL CLIENTE PIDE UNA INVESTIGACIÓN DINÁMICA
        if "investig" in mensaje_usuario or "reporte" in mensaje_usuario:
            
            # 1. Extraemos qué quiere buscar el usuario
            query_busqueda = mensaje_usuario.replace("investiga", "").replace("reporte", "").replace("de", "").strip()
            if not query_busqueda:
                query_busqueda = "negocios locales"
                
                                    # 1. Buscamos en Google Maps (Google Places API)
            resultados_maps = buscar_negocios_locales(query_busqueda, google_api_key)
            
            if resultados_maps:
                info_lugares = "DATOS REALES EXTRAÍDOS:\n"
                p = resultados_maps[0] 
                nombre = p.get('displayName', {}).get('text', 'Sin nombre')
                web = p.get('websiteUri', 'No tiene página web oficial')
                tel = p.get('nationalPhoneNumber', 'No tiene teléfono público')
                direccion = p.get('formattedAddress', 'Dirección no especificada')
                rating = p.get('rating', 'Sin calificación')
                reviews = p.get('userRatingCount', '0')
                
                # Disparamos el francotirador web para analizar su página
                datos_scrap = francotirador_web(web)
                
                info_lugares += f"- Negocio: {nombre}\n- Dirección: {direccion}\n- Web: {web}\n- Teléfono: {tel}\n- Calificación: {rating} estrellas (basado en {reviews} reseñas)\n"
                info_lugares += f"- Espionaje Web: {datos_scrap}\n"
            else:
                info_lugares = "No se encontraron datos exactos en Maps."

                        # 2. EL NUEVO CEREBRO: ARQUITECTO DE SOLUCIONES
            instrucciones_sistema = """Eres BigaBot, el Arquitecto de Soluciones de BigaEstudio. Tu objetivo es auditar negocios locales en Chile y entregar dos cosas en tu misma respuesta: un reporte sutil para el cliente, y un plan técnico interno para Bastián.

ESTRUCTURA EXACTA DE TU RESPUESTA (Debes usar estas etiquetas exactas):

[REPORTE CLIENTE]
Redacta 3 párrafos sutiles, profesionales y analíticos para el dueño del negocio.
Párrafo 1: Observación objetiva. Menciona su negocio y sus datos (reseñas, web). Valida su esfuerzo actual (ej. si tienen web o WhatsApp), pero muestra la deficiencia técnica de forma sutil.
Párrafo 2: El cuello de botella. Explica con lógica cómo esa fricción les hace perder ventas (ej. clientes nocturnos que no pueden comprar). Calcula una pérdida realista en CLP (ej. $200.000 a $400.000 mensuales en cotizaciones perdidas).
Párrafo 3: Invitación profesional. Invítalos a una charla exploratoria de 10 minutos para evaluar cómo optimizar ese sistema. Cero presión, actúa como un consultor que viene a solucionar fugas.
Usa la etiqueta HTML <b>texto</b> para resaltar los datos.

[PLAN INTERNO]
Háblale directo a Bastián (tu jefe). Dale 3 viñetas tácticas con el "Plano de Ensamblaje" para este cliente.
Ejemplo de formato: 
- 🛠️ Herramienta Sugerida: [Qué usar, ej. WooCommerce, Zapier].
- ⚙️ Solución Técnica: [Qué conectar con qué].
- 💡 Ángulo de Charla: [De qué hablar si el cliente acepta la reunión].
"""

            prompt_auditoria = f"Analiza esta data de la búsqueda '{query_busqueda}':\n{info_lugares}\n\nGenera el reporte sutil y el plan interno."
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": instrucciones_sistema},
                    {"role": "user", "content": prompt_auditoria}
                ],
               model="llama-3.1-70b-versatile",

            )

            respuesta_completa = chat_completion.choices[0].message.content
            
            # 3. Separamos el reporte del cliente del plan de Bastián
            if "[PLAN INTERNO]" in respuesta_completa:
                partes = respuesta_completa.split("[PLAN INTERNO]")
                texto_pdf = partes[0].replace("[REPORTE CLIENTE]", "").strip()
                plan_interno = "Tu Plano de Ensamblaje Técnico:\n\n" + partes[1].strip()
            else:
                texto_pdf = respuesta_completa
                plan_interno = "Nota: La IA no separó el plan interno. Revisa el PDF para la data."

            # 4. Inyectamos solo el reporte sutil en el PDF
            crear_pdf_prospeccion(texto_pdf, "Reporte_BigaEstudio.pdf", "logo.png")
            
            # 5. Enviamos el PDF y el Plan Interno por WhatsApp
            url_pdf = "https://bigabot-agente.onrender.com/descargar-pdf" # Ajusta tu URL si es distinta
            texto_chat = f"¡Análisis completado, Bastián! 🚀\n\n{plan_interno}"
            
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Message>
                    <Body>{texto_chat}</Body>
                    <Media>{url_pdf}</Media>
                </Message>
            </Response>"""
            
            if remitente in memoria_usuarios:
                del memoria_usuarios[remitente] # Limpiamos memoria
                
            return Response(content=xml_response, media_type="application/xml")

            
        # MODO 2: CHAT CONTINUO (Consultas normales)
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
            <Message><Body>Dame un segundo que estoy procesando demasiada información. Volvamos a intentarlo.</Body></Message>
        </Response>"""
        return Response(content=error_xml, media_type="application/xml")


# 6. Arranque del Servidor (El motor que le faltaba a Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
