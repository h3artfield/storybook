from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
from PIL import Image
import os


def create_pdf(folder_path, title, num_pages):
    pdf_filename = os.path.join(folder_path, f"{title}_book.pdf")
    c = canvas.Canvas(pdf_filename, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Define text style
    styles = getSampleStyleSheet()
    text_style = ParagraphStyle('CustomStyle',
                                parent=styles['Normal'],
                                alignment=TA_CENTER,
                                fontSize=18,  # Increased font size
                                leading=24,  # Space between lines (1.5 times the font size)
                                spaceAfter=10)  # Extra space after paragraphs

    for page_num in range(1, num_pages + 1):
        # Add text
        text_filename = os.path.join(folder_path, f"page_{page_num}_text.txt")
        if os.path.exists(text_filename):
            with open(text_filename, 'r') as f:
                text = f.read()

            # Replace newlines with <br/> tags for proper line breaks
            text = text.replace('\n', '<br/>')

            # Create a paragraph with the text
            p = Paragraph(text, text_style)

            # Get the width and height of the text
            text_width, text_height = p.wrap(width / 2 - 2 * inch, height - 2 * inch)

            # Draw the text, centered on the left half
            p.drawOn(c, inch, (height - text_height) / 2)

        # Add illustration
        img_filename = os.path.join(folder_path, f"page_{page_num}_illustration.png")
        if os.path.exists(img_filename):
            img = Image.open(img_filename)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)

            # Calculate the maximum possible width and height for the image
            max_img_width = width / 2 - 0.5 * inch
            max_img_height = height - 0.5 * inch

            # Determine the actual display size while maintaining aspect ratio
            if max_img_width / max_img_height > aspect:
                display_height = max_img_height
                display_width = display_height / aspect
            else:
                display_width = max_img_width
                display_height = display_width * aspect

            # Calculate position to center the image on the right half
            x_position = width / 2 + (width / 2 - display_width) / 2
            y_position = (height - display_height) / 2

            c.drawImage(img_filename, x_position, y_position,
                        width=display_width, height=display_height)

        c.showPage()

    c.save()
    print(f"PDF created: {pdf_filename}")

# Usage
folder_path = "C:/Users/h3art/PycharmProjects/kbc/kbc/_The Portal Beneath_ Chronicles of the Serpent Lord_"  # Replace with the actual path to your book folder
title = "CSL"  # Replace with your actual book title
create_pdf(folder_path, title, 20)