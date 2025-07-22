from flask import Flask, request, send_file, render_template
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color
import io
from datetime import datetime
import os

app = Flask(__name__)

def create_watermark(date_str: str) -> tuple:
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    # Format date
    short_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")

    # Watermark styling
    can.saveState()
    can.translate(300, 400)
    can.rotate(45)

    # "PAID" text – bigger
    can.setFont("Helvetica-Bold", 72)
    can.setFillColor(Color(0.8, 0.1, 0.1, alpha=0.3))  # Semi-transparent red
    can.drawCentredString(0, 30, "PAID")

    # Short date – bigger and closer
    can.setFont("Helvetica-Bold", 36)
    can.setFillColor(Color(0.8, 0.1, 0.1, alpha=0.3))
    can.drawCentredString(0, -20, short_date)

    can.restoreState()
    can.save()
    return packet.getvalue(), short_date

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    pdf_file = request.files["pdfFile"]
    paid_date = request.form["paidDate"]

    watermark_pdf, short_date = create_watermark(paid_date)
    watermark_page = PdfReader(io.BytesIO(watermark_pdf)).pages[0]

    reader = PdfReader(pdf_file)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    # Rename output: originalname - paid on DD-MM-YYYY.pdf
    original_name = os.path.splitext(pdf_file.filename)[0]
    output_filename = f"{original_name} - paid on {short_date}.pdf"
    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return send_file(
        output_stream,
        download_name=output_filename,
        as_attachment=True,
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)