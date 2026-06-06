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

            # 2. EL NUEVO CEREBRO DE VENTAS
            instrucciones_sistema = """Eres BigaBot, el auditor estratégico B2B de BigaEstudio. Tu objetivo es redactar un reporte de diagnóstico de 3 párrafos para dueños de negocios locales chilenos. No estás aquí para venderles inmediatamente, sino para mostrarles su realidad, filtrar si son buenos clientes y generar curiosidad para una primera reunión.

REGLAS DE ORO (Si las rompes, fracasas):
1. NUNCA escribas "Párrafo 1", "Diagnóstico", "Solución" ni ningún subtítulo. Escribe solo el texto corrido separado por saltos de línea.
2. SÉ REALISTA CON EL DINERO: Nada de "millones diarios". Habla de perder 2 o 3 buenas cotizaciones al mes por culpa de su invisibilidad digital (ej. entre $200.000 y $600.000 CLP mensuales). Usa montos que un dueño de local chileno sienta reales.
3. NO VENDAS, FILTRA: No ofrezcas servicios específicos, ni garantías exageradas, ni precios. Posiciónate como una agencia que busca aliados estratégicos y que no trabaja con cualquiera.
4. Usa la etiqueta HTML <b>texto</b> para resaltar los datos extraídos y los montos de dinero.

ESTRUCTURA OBLIGATORIA (Solo redacta los textos):
[Párrafo 1 - La Radiografía Real]: Menciona su negocio y los datos extraídos de Google (estrellas, reseñas, falta de web/redes). Muéstrales con crudeza pero respeto lo que sus clientes ven hoy. Hazles notar el costo invisible: la fuga real de dinero mensual porque la gente confía más en la competencia que sí aparece y se ve profesional en internet.
[Párrafo 2 - El Cambio de Paradigma]: Explica que el problema no es la calidad de sus productos, sino su "vitrina digital". Menciona que en BigaEstudio transformamos negocios estancados en referentes de su zona, pero aclara que somos selectivos y solo trabajamos con dueños de negocios que realmente tienen la mentalidad para escalar.
[Párrafo 3 - La Invitación Filtro]: No intentes cerrar una venta. Haz un llamado a la acción de bajo compromiso. Invítalos a responder el mensaje para agendar una breve charla exploratoria de 10 minutos. Diles que el objetivo es simplemente ver si hay "fit" (compatibilidad) para trabajar juntos, sin presiones ni compromisos.
"""


            prompt_auditoria = f"Analiza esta data de la búsqueda '{query_busqueda}':\n{info_lugares}\n\nGenera el reporte directo y persuasivo."
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": instrucciones_sistema},
                    {"role": "user", "content": prompt_auditoria}
                ],
                model="llama-3.1-8b-instant",
            )

            
            texto_reporte = chat_completion.choices[0].message.content
            
            # 4. Inyectamos la inteligencia de Groq en el PDF con tu logo
            crear_pdf_prospeccion(texto_reporte, "Reporte_BigaEstudio.pdf", "logo.png")
            
            # 5. Enviamos el PDF por WhatsApp
            texto_chat = f"¡Auditoría completada con éxito! 🚀 Analicé los datos reales y generé tu reporte estratégico de {query_busqueda}. Aquí lo tienes:"
            url_pdf = "https://bigabot-agente.onrender.com/descargar-pdf" # Ajusta tu URL si es distinta
            
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
