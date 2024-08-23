import fitz  # PyMuPDF
import io
import os
import json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color

# Load the local dictionary file
with open('dic.json', encoding='utf-8') as f:
    dic = json.load(f)

def create_text_layer(text, width, height):
    """Create a PDF with a text layer to overlay on an existing PDF."""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(int(width), int(height)))

    pdfmetrics.registerFont(TTFont('THSarabunNew', 'THSarabunNew.ttf'))
    
    can.setFillColor(Color(0, 0, 0, alpha=0.5))  # 50% opacity
    text_object = can.beginText(10, int(height) - 50)
    text_object.setFont("THSarabunNew", 12)
    text_object.setFillColorRGB(1, 1, 1)  # White color

    max_width = int(width) - 20
    words = text.replace('\n', ' \n ').split(' ')
    line = ''

    for word in words:
        if word == '\n':
            text_object.textLine(line)
            line = ''
        else:
            test_line = f"{line} {word}".strip()
            if can.stringWidth(test_line, "THSarabunNew", 12) <= max_width:
                line = test_line
            else:
                text_object.textLine(line)
                line = word

    if line:
        text_object.textLine(line)
    
    can.drawText(text_object)
    can.save()
    packet.seek(0)
    
    return packet

def add_searchable_text_to_pdf(input_pdf_path, output_pdf_path, text_dict):
    """Add a searchable text layer to a PDF based on provided text dictionary."""
    try:
        doc = fitz.open(input_pdf_path)
        for page_num, page in enumerate(doc):
            try:
                page_text = text_dict['pages'][page_num]['text']
                if page_text:
                    width, height = page.rect.width, page.rect.height
                    packet = create_text_layer(page_text, width, height)
                    new_pdf = fitz.open(stream=packet.getvalue(), filetype="pdf")
                    page.show_pdf_page(page.rect, new_pdf, 0)
            except Exception as page_err:
                print(f"Error processing page {page_num} of {input_pdf_path}: {page_err}")

        doc.save(output_pdf_path)
    
    except Exception as e:
        print(f"Error processing {input_pdf_path}: {e}")
        with open('error_log.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"Error processing {input_pdf_path}: {e}\n")

# Process each PDF in the dictionary
for pdf_data in dic:
    input_pdf_path = pdf_data['path']
    output_dir = os.path.join('output_pdf', os.path.relpath(os.path.dirname(input_pdf_path), start='C:\\JobNSTDAOCR\\t1'))

    os.makedirs(output_dir, exist_ok=True)
    output_pdf_path = os.path.join(output_dir, os.path.basename(input_pdf_path))

    add_searchable_text_to_pdf(input_pdf_path, output_pdf_path, pdf_data)
    print(f"Processed {os.path.basename(input_pdf_path)} saved to {output_dir}")
