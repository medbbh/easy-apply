from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import os
from datetime import datetime
from typing import Optional

class PDFService:
    def __init__(self):
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_resume_pdf(self, content: str, filename: Optional[str] = None) -> str:
        if filename is None:
            filename = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Basic CSS for resume
        css = CSS(string='''
            @page {
                margin: 1cm;
                size: letter;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 0.5em;
            }
            h2 {
                color: #2c3e50;
                margin-top: 1em;
            }
            .section {
                margin-bottom: 1em;
            }
            .experience-item {
                margin-bottom: 1em;
            }
            .skills-list {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5em;
            }
            .skill {
                background: #f0f0f0;
                padding: 0.2em 0.5em;
                border-radius: 3px;
            }
        ''')

        # Convert content to HTML
        html_content = f"""
        <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {content}
            </body>
        </html>
        """

        # Generate PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        output_path = os.path.join(self.output_dir, filename)
        
        html.write_pdf(
            output_path,
            stylesheets=[css],
            font_config=font_config
        )

        return output_path

    def generate_cover_letter_pdf(self, content: str, filename: Optional[str] = None) -> str:
        if filename is None:
            filename = f"cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Basic CSS for cover letter
        css = CSS(string='''
            @page {
                margin: 2.5cm;
                size: letter;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .header {
                text-align: right;
                margin-bottom: 2em;
            }
            .date {
                margin-bottom: 2em;
            }
            .recipient {
                margin-bottom: 2em;
            }
            .content {
                text-align: justify;
            }
            .signature {
                margin-top: 2em;
            }
        ''')

        # Convert content to HTML
        html_content = f"""
        <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {content}
            </body>
        </html>
        """

        # Generate PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        output_path = os.path.join(self.output_dir, filename)
        
        html.write_pdf(
            output_path,
            stylesheets=[css],
            font_config=font_config
        )

        return output_path 