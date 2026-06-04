import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY

def crear_pdf_prospeccion(texto_dinamico, nombre_archivo="Reporte_BigaEstudio.pdf", logo_path="logo.png"):
    # 1. Reducimos márgenes para que el banner se vea imponente
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    estilo_normal = styles["Normal"]
    estilo_normal.alignment = TA_JUSTIFY
    estilo_normal.fontSize = 11
    estilo_normal.leading = 16 # Más espacio entre líneas para lectura fácil
    
    elementos = []

    # 2. El Banner Superior
    if os.path.exists(logo_path):
        ancho_banner = 532 # Ancho exacto de la hoja sin los márgenes
        alto_banner = 70   # Altura sutil de barra
        imagen = Image(logo_path, width=ancho_banner, height=alto_banner)
        imagen.preserveAspectRatio = False # Forzamos que se estire como barra
        elementos.append(imagen)
        elementos.append(Spacer(1, 25))

    # 3. Procesar el texto inteligente (Soporte para Negritas HTML)
    parrafos = texto_dinamico.split('\n')
    for p in parrafos:
        if p.strip() != "":
            # Limpiamos asteriscos por si a la IA se le escapan
            texto_limpio = p.strip().replace('**', '').replace('*', '')
            elementos.append(Paragraph(texto_limpio, estilo_normal))
            elementos.append(Spacer(1, 10))

    doc.build(elementos)
