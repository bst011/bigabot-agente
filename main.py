from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
import google.generativeai as genai
import os
from pdf_generator import crear_pdf_prospeccion

app = FastAPI()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# --- 🧠 EL CEREBRO DE MEMORIA ---
# Este diccionario guardará el historial de cada número de teléfono
memoria_usuarios = {}

@app.get("/")
def home():
    return {"mensaje": "Servidor de BigaEstudio. Escuchando WhatsApp con memoria..."}

@app.get("/descargar-pdf")
def entregar_pdf():
    return FileResponse("Reporte_BigaEstudio.pdf", media_type='application/pdf', filename="Prospeccion_BigaEstudio.pdf")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        mensaje_usuario = form_data.get('Body', '').lower()
        remitente = form_data.get('From', '') # Detectamos el número de celular que escribe

        # Configuramos la IA y le damos su "alma" base
            instrucciones_base = """
    Eres BigaBot, estratega principal de adquisición y auditoría B2B de la agencia BigaEstudio. Tu objetivo es analizar negocios locales y detectar oportunidades urgentes de digitalización o automatización. Me enviarás los reportes directamente por WhatsApp.
    
    REGLAS:
    1. Evalúa fricción: ¿Tienen web? ¿Tienen enlace directo a WhatsApp? Si no lo tienen, es una falla crítica en su sistema de ventas.
    2. Estructura estricta: Tu respuesta DEBE contener solo 3 cosas: Nombre del Negocio, Diagnóstico (el problema detectado) y Ángulo de Venta Recomendado (ej: Bot de WhatsApp o Ecosistema Web).
    3. Formato para WhatsApp: NO uses asteriscos ni negritas de Markdown bajo ninguna circunstancia. Usa texto plano, guiones para listar y un par de emojis para separar la información.
    4. Sé ultra directo, sin saludos largos. Máximo 3 párrafos cortos.
    """
        
        # Buscamos el modelo correcto
        nombre_modelo = 'gemini-1.0-pro'
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nombre_modelo = m.name
                break
                
        model = genai.GenerativeModel(
            model_name=nombre_modelo,
            system_instruction=instrucciones_base
        )

        # MODO 1: EL CLIENTE PIDE UNA INVESTIGACIÓN (Bypass Temporal)
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
            
            # Borramos la memoria de este usuario para que no se confunda tras el PDF
            if remitente in memoria_usuarios:
                del memoria_usuarios[remitente]
                
            return Response(content=xml_response, media_type="application/xml")

        # MODO 2: CHAT CONTINUO CON MEMORIA
        else:
            # 1. Si el número es nuevo, le creamos su expediente en blanco
            if remitente not in memoria_usuarios:
                memoria_usuarios[remitente] = []

            # 2. Iniciamos un hilo de chat pasándole TODO su historial
            chat = model.start_chat(history=memoria_usuarios[remitente])
            
            # 3. Enviamos el mensaje actual
            respuesta_ia = chat.send_message(mensaje_usuario)
            
            # 4. Actualizamos el expediente en nuestro servidor con la nueva charla
            memoria_usuarios[remitente] = chat.history
            
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
            <Message><Body>Dame un segundo que estoy procesando demasiada información. Volvamos a intentarlo.</Body></Message>
        </Response>"""
        return Response(content=error_xml, media_type="application/xml")