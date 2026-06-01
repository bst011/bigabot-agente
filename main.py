from fastapi import FastAPI, Request, Response
import google.generativeai as genai
import os
import traceback

app = FastAPI()

# Conectar el cerebro de la IA
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio Activo. Escuchando WhatsApp..."}

# --- NUEVO: EL OÍDO DE WHATSAPP ---
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        # 1. Leemos el mensaje que nos envía Twilio
        form_data = await request.form()
        mensaje_usuario = form_data.get('Body', '')
        remitente = form_data.get('From', '')
        
        print(f"Mensaje recibido de {remitente}: {mensaje_usuario}")

        # 2. Despertamos a Gemini
        nombre_modelo = 'gemini-1.0-pro'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nombre_modelo = m.name
                break
        model = genai.GenerativeModel(nombre_modelo)
        
        # 3. Le damos el contexto de chat a la IA
        prompt = f"""
        Actúa como BigaBot, el asistente de inteligencia artificial de la agencia BigaEstudio.
        Un cliente te acaba de escribir esto por WhatsApp: "{mensaje_usuario}"
        
        Si te pide investigar un nicho o buscar negocios, nombra 3 negocios de ese rubro que existan en Chile, menciona un error visual común que tienen, y cómo BigaEstudio lo solucionaría con un manual de identidad.
        Si solo te saluda o hace una pregunta general, responde de manera carismática, profesional y breve, presentándote como el asesor de crecimiento de la agencia.
        REGLA ESTRICTA: Escribe en texto plano. NO uses formato Markdown, ni negritas, ni asteriscos (*), ni guiones largos, para que se lea perfecto en WhatsApp.
        """
        
        respuesta_ia = model.generate_content(prompt)
        texto_respuesta = respuesta_ia.text
        
        # 4. Empaquetamos la respuesta en el formato que exige Twilio (XML/TwiML)
        xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>{texto_respuesta}</Message>
        </Response>"""
        
        return Response(content=xml_response, media_type="application/xml")

    except Exception as e:
        print(f"Error técnico: {e}")
        error_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>BigaBot está actualizando sus sistemas. Por favor, intenta de nuevo en unos minutos.</Message>
        </Response>"""
        return Response(content=error_xml, media_type="application/xml")