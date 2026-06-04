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

def buscar_negocios_locales(query, api_key):
    try:
        url = "https://places.googleapis.com/v1/places:searchText"
        
        # Le pedimos a Google el combo completo de datos
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.websiteUri,places.nationalPhoneNumber,places.rating,places.userRatingCount,places.formattedAddress"
        }
        
        data = {"textQuery": query}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json().get('places', [])
        else:
            return []
    except:
        return []


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
        instrucciones_sistema = "Eres BigaBot, estratega principal de adquisición B2B de BigaEstudio. Tienes una personalidad muy entusiasta, proactiva y enérgica, pero mantienes una responsabilidad técnica intachable. Tu objetivo es auditar negocios y detectar oportunidades de digitalización. REGLAS: 1. Evalúa críticamente si tienen web o WhatsApp. 2. Estructura: Nombre del Negocio, Diagnóstico, y Ángulo de Venta. 3. NO uses Markdown bajo ninguna circunstancia. 4. Sé claro y directo."

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
                # Nos enfocamos en el primer resultado para hacer un reporte hiper-personalizado
                p = resultados_maps[0] 
                nombre = p.get('displayName', {}).get('text', 'Sin nombre')
                web = p.get('websiteUri', 'No tiene página web oficial')
                tel = p.get('nationalPhoneNumber', 'No tiene teléfono público')
                direccion = p.get('formattedAddress', 'Dirección no especificada')
                rating = p.get('rating', 'Sin calificación')
                reviews = p.get('userRatingCount', '0')
                
                info_lugares += f"- Negocio: {nombre}\n- Dirección: {direccion}\n- Web: {web}\n- Teléfono: {tel}\n- Calificación: {rating} estrellas (basado en {reviews} reseñas)\n"
            else:
                info_lugares = "No se encontraron datos exactos en Maps."

            # 2. EL NUEVO CEREBRO DE VENTAS
            instrucciones_sistema = """Eres BigaBot, el auditor B2B más letal y persuasivo de BigaEstudio. 
            Redacta un reporte de auditoría digital que haga que el dueño del negocio sienta urgencia por digitalizarse contigo.
            REGLAS ESTRICTAS:
            1. Usa la fórmula de ventas PAS (Problema - Agitación - Solución). No seas 'amable', evidencia el dinero que están perdiendo.
            2. Usa los datos reales proporcionados (estrellas, cantidad de opiniones, falta de web). Úsalos para demostrar autoridad.
            3. FORMATO VISUAL: Usa la etiqueta HTML <b>texto</b> para resaltar palabras clave o métricas. NO uses markdown (ni asteriscos, ni numerales).
            4. Estructura el reporte exactamente así:
               <b>DIAGNÓSTICO INICIAL</b>
               [Texto del problema]
               
               <b>EL IMPACTO (LO QUE ESTÁS PERDIENDO)</b>
               [Agitación del problema usando los datos]
               
               <b>PLAN DE ACCIÓN BIGAESTUDIO</b>
               [La solución directa]"""

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