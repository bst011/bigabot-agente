import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

def crear_pdf_prospeccion(texto_dinamico, nombre_archivo="Reporte_BigaEstudio.pdf", logo_path="logo.png"):
    # Configuramos el documento
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    estilo_normal = styles["Normal"]
    estilo_normal.alignment = TA_JUSTIFY
    estilo_normal.fontSize = 11
    estilo_normal.leading = 15 # Espaciado entre líneas
    
    elementos = []

    # 1. Inyectar el Header (Logo) si el archivo existe
    if os.path.exists(logo_path):
        imagen = Image(logo_path, width=450, height=250)
        imagen.preserveAspectRatio = True
        elementos.append(imagen)
        elementos.append(Spacer(1, 30)) # Espacio entre logo y texto
    else:
        print("Advertencia: No se encontró logo.png")

    # 2. Inyectar el texto dinámico de Groq
    parrafos = texto_dinamico.split('\n')
    for p in parrafos:
        if p.strip() != "":
            # Convertimos el texto plano a un formato que el PDF entienda
            texto_limpio = p.strip().replace('*', '') # Limpieza de seguridad
            elementos.append(Paragraph(texto_limpio, estilo_normal))
            elementos.append(Spacer(1, 12))

    # Construir el PDF
    doc.build(elementos)
