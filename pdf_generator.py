from fpdf import FPDF

class BigaPDF(FPDF):
    def header(self):
        self.set_fill_color(58, 31, 74)
        self.rect(0, 0, 210, 30, 'F')
        self.set_font("helvetica", "B", 14)
        self.set_text_color(212, 175, 55)
        self.cell(0, 10, "BIGAESTUDIO | INVESTIGACION DE MERCADO", border=0, align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Generado autonomamente por BigaBot v1.0", align="C")

def crear_pdf_prospeccion(texto_ia, nombre_salida):
    pdf = BigaPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.set_text_color(40, 40, 40)

    for linea in texto_ia.split('\n'):
        if linea.startswith('##') or linea.startswith('**'):
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(58, 31, 74)
            pdf.ln(5)
            pdf.cell(0, 8, txt=linea.replace('##', '').replace('**', '').strip(), ln=1)
            pdf.set_font("helvetica", size=11)
            pdf.set_text_color(40, 40, 40)
        elif linea.startswith('-') or linea.startswith('*'):
            pdf.multi_cell(0, 6, txt=f"  • {linea[1:].strip()}")
        elif linea.strip():
            pdf.multi_cell(0, 6, txt=linea.strip())
            pdf.ln(2)

    pdf.output(nombre_salida)

