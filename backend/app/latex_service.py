import os
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional
import re
from datetime import datetime

class LaTeXService:
    def __init__(self):
        self.latex_template = r"""
\documentclass[11pt, letterpaper]{article}

% Packages:
\usepackage[
    ignoreheadfoot,
    top=2.5cm,
    bottom=2.5cm,
    left=2.5cm,
    right=2.5cm,
    footskip=1.2cm,
]{geometry} 
\usepackage{titlesec}
\usepackage{tabularx}
\usepackage{array}
\usepackage[dvipsnames]{xcolor}
\definecolor{primaryColor}{RGB}{0, 0, 0}
\usepackage{enumitem}
\usepackage{fontawesome5}
\usepackage{hyperref}
\hypersetup{colorlinks=true, urlcolor=primaryColor}
\usepackage{bookmark}
\usepackage{lastpage}
\usepackage{paracol}
\usepackage{charter}
\usepackage{setspace}
\onehalfspacing

\raggedright
\pagestyle{empty}
\setcounter{secnumdepth}{0}
\setlength{\parindent}{0pt}
\setlength{\columnsep}{0.3cm}
\pagenumbering{gobble}

\titleformat{\section}{\bfseries\large}{}{0pt}{}[\vspace{2pt}\titlerule]
\titlespacing{\section}{-1pt}{0.4cm}{0.3cm}

\begin{document}

<<CONTENT>>

\end{document}
"""

    def escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters in text."""
        if not text:
            return ""
        
        # Dictionary of LaTeX special characters and their escaped versions
        special_chars = {
            '\\': r'\textbackslash{}',
            '{': r'\{',
            '}': r'\}',
            '$': r'\$',
            '&': r'\&',
            '#': r'\#',
            '^': r'\^{}',
            '_': r'\_',
            '~': r'\textasciitilde{}',
            '%': r'\%',
        }
        
        # First escape backslashes
        text = text.replace('\\', r'\textbackslash{}')
        
        # Then escape other special characters
        for char, escaped in special_chars.items():
            if char != '\\':  # Already handled
                text = text.replace(char, escaped)
        
        return text

    def generate_resume_latex(self, user_info: Dict, job_specific_content: Optional[Dict] = None) -> str:
        """Generate a LaTeX resume based on user information."""
        
        # Ensure job_specific_content is a dictionary
        if job_specific_content is None:
            job_specific_content = {}
        elif not isinstance(job_specific_content, dict):
            print(f"Warning: job_specific_content is not a dict, it's {type(job_specific_content)}: {job_specific_content}")
            job_specific_content = {}
        
        # Extract user data with safe defaults
        name = self.escape_latex(user_info.get('full_name', 'Your Name'))
        email = user_info.get('email', 'email@example.com')
        phone = self.escape_latex(user_info.get('phone', '+1234567890'))
        linkedin = user_info.get('linkedin', '')
        github = user_info.get('github', '')
        
        summary = self.escape_latex(job_specific_content.get('summary', user_info.get('summary', '')))
        education = user_info.get('education', [])
        experience = user_info.get('experience', [])
        skills = user_info.get('skills', {})
        projects = user_info.get('projects', [])
        certifications = user_info.get('certifications', [])
        
        # Build the resume content
        content = []
        
        # Header
        header = f"""\\begin{{center}}
    \\fontsize{{22pt}}{{22pt}}\\selectfont \\textbf{{{name}}}
    \\vspace{{8pt}}

    \\normalsize
    \\faEnvelope\\ \\href{{mailto:{email}}}{{{email}}} \\quad
    \\faPhone\\ {phone}"""
        
        if linkedin:
            linkedin_clean = linkedin.replace('https://www.linkedin.com/in/', '').strip('/')
            header += f"""\\\\
    \\faLinkedin\\ \\href{{https://www.linkedin.com/in/{linkedin_clean}/}}{{{self.escape_latex(linkedin_clean)}}}"""
        
        if github:
            github_clean = github.replace('https://github.com/', '').strip('/')
            header += f""" \\quad
    \\faGithub\\ \\href{{https://github.com/{github_clean}}}{{{self.escape_latex(github_clean)}}}"""
        
        header += "\n\\end{center}"
        content.append(header)
        
        # Professional Summary
        if summary:
            content.append(f"""
\\section{{Professional Summary}}
{summary}""")
        
        # Education
        if education:
            edu_section = "\n\\section{Education}"
            for edu in education:
                # Ensure edu is a dictionary
                if not isinstance(edu, dict):
                    print(f"Warning: education item is not a dict: {type(edu)} - {edu}")
                    if isinstance(edu, str):
                        edu = {'degree': edu, 'school': '', 'dates': ''}
                    else:
                        continue
                        
                degree = self.escape_latex(edu.get('degree', ''))
                school = self.escape_latex(edu.get('school', ''))
                dates = self.escape_latex(edu.get('dates', ''))
                if degree and school:
                    edu_section += f"\n\\textbf{{{degree}}}, {school} \\hfill {dates}\\\\"
            content.append(edu_section)
        
        # Experience
        if experience:
            exp_section = "\n\\section{Experience}"
            for exp in experience:
                # Ensure exp is a dictionary
                if not isinstance(exp, dict):
                    print(f"Warning: experience item is not a dict: {type(exp)} - {exp}")
                    if isinstance(exp, str):
                        exp = {'title': 'Position', 'company': 'Company', 'dates': '', 'bullets': [exp]}
                    else:
                        continue
                        
                title = self.escape_latex(exp.get('title', ''))
                company = self.escape_latex(exp.get('company', ''))
                dates = self.escape_latex(exp.get('dates', ''))
                technologies = self.escape_latex(exp.get('technologies', ''))
                bullets = exp.get('bullets', [])
                
                if title and company:
                    exp_section += f"\n\n\\textbf{{{title}}}, {company} \\hfill {dates}\\\\"
                    if technologies:
                        exp_section += f"\n\\textbf{{Technologies}}: {technologies}\\\\"
                    
                    if bullets:
                        exp_section += "\n\\begin{itemize}[noitemsep,topsep=0pt]"
                        for bullet in bullets:
                            exp_section += f"\n    \\item {self.escape_latex(bullet)}"
                        exp_section += "\n\\end{itemize}"
            content.append(exp_section)
        
        # Projects
        if projects:
            proj_section = "\n\\section{Projects}"
            for proj in projects:
                # Ensure proj is a dictionary
                if not isinstance(proj, dict):
                    print(f"Warning: project item is not a dict: {type(proj)} - {proj}")
                    if isinstance(proj, str):
                        proj = {'name': proj, 'technologies': '', 'date': '', 'bullets': []}
                    else:
                        continue
                        
                name = self.escape_latex(proj.get('name', ''))
                technologies = self.escape_latex(proj.get('technologies', ''))
                date = self.escape_latex(proj.get('date', ''))
                bullets = proj.get('bullets', [])
                
                if name:
                    proj_section += f"\n\n\\textbf{{{name}}} \\hfill {date}\\\\"
                    if technologies:
                        proj_section += f"\n\\textbf{{Technologies}}: {technologies}\\\\"
                    
                    if bullets:
                        proj_section += "\n\\begin{itemize}[noitemsep,topsep=0pt]"
                        for bullet in bullets:
                            proj_section += f"\n    \\item {self.escape_latex(bullet)}"
                        proj_section += "\n\\end{itemize}"
            content.append(proj_section)
        
        # Technical Skills
        if skills:
            skills_section = "\n\\section{Technical Skills}"
            # Ensure skills is a dictionary
            if not isinstance(skills, dict):
                print(f"Warning: skills is not a dict: {type(skills)} - {skills}")
                if isinstance(skills, list):
                    # Convert list to dict
                    skills = {'Skills': skills}
                elif isinstance(skills, str):
                    # Convert string to dict
                    skills = {'Skills': [skills]}
                else:
                    skills = {}
            
            for category, items in skills.items():
                if items:
                    category_name = self.escape_latex(category)
                    # Ensure items is a list or string
                    if isinstance(items, list):
                        items_text = self.escape_latex(', '.join(str(item) for item in items))
                    else:
                        items_text = self.escape_latex(str(items))
                    skills_section += f"\n\\textbf{{{category_name}}}: {items_text}\\\\"
            content.append(skills_section)
        
        # Certifications
        if certifications:
            cert_section = "\n\\section{Certifications and Training}"
            for cert in certifications:
                # Ensure cert is a dictionary
                if not isinstance(cert, dict):
                    print(f"Warning: certification item is not a dict: {type(cert)} - {cert}")
                    if isinstance(cert, str):
                        cert = {'name': cert, 'issuer': '', 'date': ''}
                    else:
                        continue
                        
                name = self.escape_latex(cert.get('name', ''))
                issuer = self.escape_latex(cert.get('issuer', ''))
                date = self.escape_latex(cert.get('date', ''))
                
                if name:
                    cert_text = f"\\textbf{{{name}}}"
                    if issuer:
                        cert_text += f", {issuer}"
                    cert_text += f" \\hfill {date}"
                    cert_section += f"\n{cert_text}\\\\"
            content.append(cert_section)
        
        # Combine all content
        resume_content = '\n'.join(content)
        
        # Replace the content placeholder in the template
        return self.latex_template.replace('<<CONTENT>>', resume_content)

    def generate_cover_letter_latex(self, user_info: Dict, job_info: Dict, cover_letter_content: str) -> str:
        """Generate a LaTeX cover letter."""
        
        # Extract user data
        name = self.escape_latex(user_info.get('full_name', 'Your Name'))
        email = user_info.get('email', 'email@example.com')
        phone = self.escape_latex(user_info.get('phone', '+1234567890'))
        address = self.escape_latex(user_info.get('address', 'Your Address'))
        
        # Extract job data
        company_name = self.escape_latex(job_info.get('company', 'Company Name'))
        position = self.escape_latex(job_info.get('title', 'Position'))
        
        # Get current date
        current_date = datetime.now().strftime('%B %d, %Y')
        
        # Build cover letter content
        content = f"""\\begin{{flushright}}
{name}\\\\
{address}\\\\
{phone}\\\\
{email}\\\\
{current_date}
\\end{{flushright}}

\\vspace{{1cm}}

{company_name}\\\\
Hiring Manager\\\\

\\vspace{{1cm}}

Dear Hiring Manager,

\\vspace{{0.5cm}}

{self.escape_latex(cover_letter_content)}

\\vspace{{0.5cm}}

Sincerely,\\\\
{name}"""
        
        # Use a simpler template for cover letters
        cover_letter_template = r"""\documentclass[11pt, letterpaper]{article}
\usepackage[top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm]{geometry}
\usepackage{charter}
\usepackage{setspace}
\onehalfspacing
\pagestyle{empty}

\begin{document}

<<CONTENT>>

\end{document}"""
        
        return cover_letter_template.replace('<<CONTENT>>', content)

    def compile_latex_to_pdf(self, latex_content: str, output_filename: str = "document.pdf") -> bytes:
        """Compile LaTeX content to PDF and return the PDF bytes."""
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write LaTeX content to file
            tex_file = os.path.join(temp_dir, "document.tex")
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF
            try:
                # Run pdflatex twice to resolve references
                for _ in range(2):
                    result = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, tex_file],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        # If pdflatex fails, try xelatex (better Unicode support)
                        result = subprocess.run(
                            ['xelatex', '-interaction=nonstopmode', '-output-directory', temp_dir, tex_file],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                
                # Read the generated PDF
                pdf_file = os.path.join(temp_dir, "document.pdf")
                if os.path.exists(pdf_file):
                    with open(pdf_file, 'rb') as f:
                        return f.read()
                else:
                    raise Exception("PDF file was not generated")
                    
            except subprocess.TimeoutExpired:
                raise Exception("LaTeX compilation timed out")
            except FileNotFoundError:
                raise Exception("LaTeX compiler (pdflatex/xelatex) not found. Please install TeX distribution.")
            except Exception as e:
                raise Exception(f"LaTeX compilation failed: {str(e)}")

    def generate_pdf_fallback(self, content: Dict, doc_type: str = 'resume') -> bytes:
        """Fallback PDF generation using weasyprint when LaTeX is not available."""
        from weasyprint import HTML, CSS
        
        if doc_type == 'resume':
            html_content = self._generate_resume_html(content)
        else:
            html_content = self._generate_cover_letter_html(content)
        
        # Generate PDF from HTML
        pdf = HTML(string=html_content).write_pdf()
        return pdf

    def _generate_resume_html(self, user_info: Dict) -> str:
        """Generate HTML resume for fallback PDF generation."""
        name = user_info.get('full_name', 'Your Name')
        email = user_info.get('email', 'email@example.com')
        phone = user_info.get('phone', '+1234567890')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Charter', 'Georgia', serif; margin: 2.5cm; line-height: 1.5; }}
                h1 {{ font-size: 22pt; text-align: center; margin-bottom: 8pt; }}
                h2 {{ font-size: 14pt; border-bottom: 2px solid #000; margin-top: 20pt; margin-bottom: 10pt; }}
                .contact {{ text-align: center; margin-bottom: 20pt; }}
                .section {{ margin-bottom: 15pt; }}
                ul {{ margin: 5pt 0; padding-left: 20pt; }}
                li {{ margin-bottom: 3pt; }}
            </style>
        </head>
        <body>
            <h1>{name}</h1>
            <div class="contact">
                {email} | {phone}
            </div>
            <div class="content">
                <!-- Resume content would be generated here -->
                <h2>Professional Summary</h2>
                <p>{user_info.get('summary', 'Professional summary...')}</p>
                
                <h2>Experience</h2>
                <p>Experience details...</p>
                
                <h2>Education</h2>
                <p>Education details...</p>
                
                <h2>Skills</h2>
                <p>Skills details...</p>
            </div>
        </body>
        </html>
        """
        return html

    def _generate_cover_letter_html(self, content: Dict) -> str:
        """Generate HTML cover letter for fallback PDF generation."""
        # Similar implementation for cover letter
        return "<html><body><h1>Cover Letter</h1><p>Cover letter content...</p></body></html>" 