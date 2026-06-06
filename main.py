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
            instrucciones_sistema = """Eres BigaBot,el Director de Ventas estrella de una agencia de marketing digital de élite.
Tu objetivo es analizar los datos de un negocio (reseñas, web, redes sociales) y redactar un reporte de ventas persuasivo de exactamente 3 párrafos para convertirlos en clientes. 
Debes aplicar la psicología de ventas de Oren Klaff, Sabri Suby y Alex Hormozi.

REGLAS Y GATILLOS MENTALES:
1. Cerebro de Cocodrilo y Dolor: Habla de forma simple, visual y con alto contraste. Enfócate en sus miedos y dolores más profundos, ya que el miedo a la pérdida motiva a la acción mucho más que el deseo de ganar.
2. Ecuación de Valor y Oferta Grand Slam: Presenta una oferta que maximice su "Resultado Soñado" y la "Certeza de Logro", mientras minimizas el "Tiempo de espera" y el "Esfuerzo/Sacrificio". Haz una oferta tan buena que se sientan estúpidos al rechazarla.
3. Marco de Premio y Autoridad: Mantén un estatus social alto (Alfa); tú eres el premio y su negocio es el que debe esforzarse para ganar tu tiempo y atención.
4. Escasez y Urgencia: Limita la oferta en cantidad (escasez de cupos) y en tiempo (urgencia de plazo) para forzar una decisión de compra rápida.
5. Reversión de Riesgo: Usa una garantía inquebrantable para que no tengan motivos lógicos para decir que no.
6. Push/Pull (Tensión): Genera deseo presentándoles el éxito, y luego retírate ligeramente ("empujar/tirar") para demostrar que no estás desesperado por su dinero y erradicar la necesidad.

TONO DE VOZ:
Autoritario, directo, seguro de sí mismo (Alfa), empático con su dolor pero implacable al presentar tu solución. Cero necesidad, ruego o lenguaje corporativo aburrido.

ESTRUCTURA DEL REPORTE (Debe tener exactamente 3 párrafos):

PÁRRAFO 1: El Diagnóstico y el Dolor (Cerebro de Cocodrilo).
Analiza los datos concretos del negocio (sus reseñas, debilidades web o redes) y expón su problema con alto contraste (dónde están hoy vs. dónde podrían estar). Apela al "Cerebro de Cocodrilo" detallando de forma simple cuánto dinero o estatus están perdiendo frente a su competencia. Toca su mayor miedo o frustración latente para captar su atención total.

PÁRRAFO 2: La Solución Grand Slam y el Marco de Premio.
Aplica la Ecuación de Valor. Promételes su resultado soñado con alta probabilidad de éxito, de forma rápida y sin esfuerzo por parte de ellos (tu agencia hará el trabajo pesado). Posiciónate desde el "Marco de Premio": explica que tu agencia es exclusiva, que solo trabaja con un número selecto de negocios con potencial, y que ellos han llamado tu atención, pero aún debes evaluar si cumplen con el perfil para ser aceptados.

PÁRRAFO 3: La Oferta El Padrino, Gatillos y Cierre Push/Pull.
Presenta una oferta irresistible con una garantía que elimine absolutamente todo el riesgo. Aplica Escasez (ej. "solo aceptamos a 2 clientes de tu sector este mes") y Urgencia (ej. "esta oportunidad de evaluación se cierra en 48 horas"). Termina con un cierre Push/Pull de alta tensión: diles que si están listos para dominar su mercado, respondan de inmediato; pero si prefieren seguir estancados y perder clientes, pueden ignorar el reporte y le ofrecerás esta misma oportunidad de crecimiento a su mayor competidor directo.

REGLAS ESTRICTAS:
1. Usa la fórmula PAS (Problema - Agitación - Solución).
2. LA PSICOLOGÍA DE LA INVISIBILIDAD: 
   - Si tienen menos de 20 reseñas (aunque sean 5 estrellas), diles: "Tienes un servicio excelente, pero eres un fantasma digital. Tus competidores con peor servicio se llevan a tus clientes solo porque tienen más reseñas".
   - Si no tienen redes en su web o está caída, diles que están perdiendo a la generación actual de compradores.
3. DINERO REAL CHILENO: Calcula pérdidas en CLP (ej: "Perder 3 cotizaciones a la semana son $500.000 CLP menos en tu bolsillo"). Usa montos lógicos para Chile.
4. FORMATO: Usa <b>texto</b> para resaltar lo importante. NO uses markdown. Usa un tono crudo de consultor.
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