from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
import google.generativeai as genai
import os
import traceback
from pdf_generator import crear_pdf_prospeccion

app = FastAPI()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio. Escuchando WhatsApp..."}

# --- NUEVO: LA VENTANILLA PARA QUE TWILIO RECOJA EL PDF ---
@app.get("/descargar-pdf")
def entregar_pdf():
    # Cuando Twilio pida el archivo, se lo entregamos en formato PDF
    return FileResponse("Reporte_BigaEstudio.pdf", media_type='application/pdf', filename="Prospeccion_BigaEstudio.pdf")

# --- EL OÍDO DE WHATSAPP ---
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        mensaje_usuario = form_data.get('Body', '').lower()
        remitente = form_data.get('From', '')

        # Configuramos la IA
        nombre_modelo = 'gemini-1.0-pro'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nombre_modelo = m.name
                break
        model = genai.GenerativeModel(nombre_modelo)

        # MODO 1: EL CLIENTE PIDE UNA INVESTIGACIÓN
        if "investig" in mensaje_usuario or "reporte" in mensaje_usuario or "pdf" in mensaje_usuario:
            
            prompt_investigacion = f"""
            Actúa como Director de Crecimiento de BigaEstudio.
            El cliente solicitó esta investigación: "{mensaje_usuario}".
            Busca en tu base de datos 3 negocios REALES en esa ubicación o rubro.
            Para cada uno detalla: Nombre real, su ubicación aproximada, el principal error en su identidad visual, y cómo BigaEstudio lo resolverá con un manual estructurado.
            REGLA ESTRICTA: Escribe en texto plano tradicional. NO uses asteriscos, ni numerales.
            """
            
            respuesta_ia = model.generate_content(prompt_investigacion)
            texto_pdf = respuesta_ia.text.encode('latin-1', 'ignore').decode('latin-1')
            
            # Fabricamos el PDF y lo guardamos temporalmente en el servidor
            crear_pdf_prospeccion(texto_pdf, "Reporte_BigaEstudio.pdf")
            
            # El mensaje de WhatsApp que acompañará al archivo
            texto_chat = "¡Listo! He analizado el mercado. Aquí tienes el reporte detallado en PDF con los negocios y nuestra propuesta estratégica. ¿Qué te parece el enfoque que le di?"
            
            # La dirección de tu "ventanilla" para que Twilio baje el PDF
            url_pdf = "https://bigabot-agente.onrender.com/descargar-pdf"
            
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Message>
                    <Body>{texto_chat}</Body>
                    <Media>{url_pdf}</Media>
                </Message>
            </Response>"""
            
            return Response(content=xml_response, media_type="application/xml")

        # MODO 2: EL CLIENTE SOLO ESTÁ CHATEANDO (Hola, preguntas, etc.)
        else:
            prompt_chat = f"""
            Eres BigaBot, estratega principal de la agencia BigaEstudio. Estás chateando por WhatsApp.
            Mensaje del cliente: "{mensaje_usuario}"
            REGLAS:
            1. HABLA COMO HUMANO: Cercano, proactivo y profesional. Cero lenguaje robótico.
            2. BREVE Y DIRECTO: Máximo 2 párrafos cortos.
            3. ENGANCHE: Termina siempre con una pregunta corta para continuar la charla.
            4. FORMATO: Usa un par de emojis. NO uses asteriscos ni negritas de Markdown.
            """
            
            respuesta_ia = model.generate_content(prompt_chat)
            
            xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Message>
                    <Body>{respuesta_ia.text}</Body>
                </Message>
            </Response>"""
            
            return Response(content=xml_response, media_type="application/xml")

    except Exception as e:
        print(f"Error técnico: {e}")
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message><Body>Hubo un pequeño cortocircuito analizando la información. Dame un minuto y volvamos a intentarlo.</Body></Message>
        </Response>"""
        return Response(content=error_xml, media_type="application/xml")