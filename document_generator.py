from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import subprocess
import os
import shutil

class DocumentGenerator:
    def __init__(self):
        self.resume_template_path = Path("templates/resume_template.tex")
        self.cover_letter_template_path = Path("templates/cover_letter_template.tex")
        self.latex_available = self._check_latex_availability()
        
    def _check_latex_availability(self) -> bool:
        try:
            result = subprocess.run(['pdflatex', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def generate_resume(self, job: Dict, job_folder: Path, user_profile: Dict = None) -> Optional[str]:
        if not user_profile:
            return self._create_plain_text_resume(job, job_folder, None)
            
        if not self.resume_template_path.exists():
            print(f"Resume template not found: {self.resume_template_path}")
            return self._create_plain_text_resume(job, job_folder, user_profile)
            
        try:
            template_content = self._load_resume_template()
            customized_content = self._customize_resume_content(template_content, job, user_profile)
            
            resume_file = job_folder / "resume.tex"
            with open(resume_file, 'w', encoding='utf-8') as f:
                f.write(customized_content)
            
            if self.latex_available:
                pdf_path = self._compile_to_pdf(resume_file)
                if pdf_path:
                    return pdf_path
            
            self._create_plain_text_resume(job, job_folder, user_profile)
            return str(resume_file)
            
        except Exception as e:
            print(f"Error generating resume: {e}")
            return self._create_plain_text_resume(job, job_folder, user_profile)
    
    def generate_cover_letter(self, job: Dict, job_folder: Path, user_profile: Dict = None) -> Optional[str]:
        if not user_profile:
            return self._create_plain_text_cover_letter(job, job_folder, None)
            
        if not self.cover_letter_template_path.exists():
            print(f"Cover letter template not found: {self.cover_letter_template_path}")
            return self._create_plain_text_cover_letter(job, job_folder, user_profile)
            
        try:
            template_content = self._load_cover_letter_template()
            customized_content = self._customize_cover_letter_content(template_content, job, user_profile)
            
            cover_letter_file = job_folder / "cover_letter.tex"
            with open(cover_letter_file, 'w', encoding='utf-8') as f:
                f.write(customized_content)
            
            if self.latex_available:
                pdf_path = self._compile_to_pdf(cover_letter_file)
                if pdf_path:
                    return pdf_path
            
            self._create_plain_text_cover_letter(job, job_folder, user_profile)
            return str(cover_letter_file)
            
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return self._create_plain_text_cover_letter(job, job_folder, user_profile)
    
    def _load_resume_template(self) -> str:
        with open(self.resume_template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_cover_letter_template(self) -> str:
        with open(self.cover_letter_template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _customize_resume_content(self, template: str, job: Dict, user_profile: Dict) -> str:
        # Extract user data
        full_name = f"{user_profile.get('firstName', '')} {user_profile.get('lastName', '')}"
        email = user_profile.get('email', '')
        phone = user_profile.get('phone', '')
        linkedin = user_profile.get('linkedin', '')
        github = user_profile.get('github', '')
        
        # Format LinkedIn and GitHub URLs
        linkedin_url = f"https://{linkedin}" if linkedin and not linkedin.startswith('http') else linkedin
        linkedin_text = linkedin.replace('linkedin.com/in/', '') if linkedin else ''
        
        github_url = f"https://{github}" if github and not github.startswith('http') else github
        github_text = github.replace('github.com/', '') if github else ''
        
        # Build sections
        education_section = self._build_education_section(user_profile.get('education', []))
        experience_section = self._build_experience_section(user_profile.get('experiences', []))
        projects_section = self._build_projects_section(user_profile.get('projects', []))
        certifications_section = self._build_certifications_section(user_profile.get('certifications', []))
        
        # Build skills sections
        skills = user_profile.get('skills', {})
        languages = ', '.join(self._prioritize_skills(skills.get('languages', []), job))
        frameworks = ', '.join(self._prioritize_skills(skills.get('frameworks', []), job))
        databases = ', '.join(skills.get('databases', []))
        tools = ', '.join(skills.get('tools', []))
        
        # Combine frameworks and backend tools
        backend_tools = [t for t in tools if any(b in t.lower() for b in ['django', 'flask', 'node', 'express', 'spring'])]
        frontend_tools = [t for t in frameworks if any(f in t.lower() for f in ['react', 'angular', 'vue', 'html', 'css'])]
        
        replacements = {
            '{FULL_NAME}': full_name,
            '{EMAIL}': email,
            '{PHONE}': phone,
            '{LINKEDIN_URL}': linkedin_url,
            '{LINKEDIN_TEXT}': linkedin_text,
            '{GITHUB_URL}': github_url,
            '{GITHUB_TEXT}': github_text,
            '{PROFESSIONAL_SUMMARY}': user_profile.get('professionalSummary', ''),
            '{EDUCATION_SECTION}': education_section,
            '{EXPERIENCE_SECTION}': experience_section,
            '{PROJECTS_SECTION}': projects_section,
            '{LANGUAGES}': languages or 'Various programming languages',
            '{FRONTEND}': ', '.join(frontend_tools) or frameworks or 'Various frontend technologies',
            '{BACKEND}': ', '.join(backend_tools) or 'Various backend technologies',
            '{DATABASES}': databases or 'Various databases',
            '{TOOLS}': tools or 'Various development tools',
            '{CERTIFICATIONS_SECTION}': certifications_section,
            '{INTERNATIONAL_EXPERIENCE}': self._build_international_experience()
        }
        
        customized_content = template
        for placeholder, value in replacements.items():
            customized_content = customized_content.replace(placeholder, value)
        
        return customized_content
    
    def _customize_cover_letter_content(self, template: str, job: Dict, user_profile: Dict) -> str:
        full_name = f"{user_profile.get('firstName', '')} {user_profile.get('lastName', '')}"
        email = user_profile.get('email', '')
        phone = user_profile.get('phone', '')
        
        replacements = {
            '{FULL_NAME}': full_name,
            '{EMAIL}': email,
            '{PHONE}': phone,
            '{TARGET_COMPANY}': job['company'],
            '{TARGET_POSITION}': job['title']
        }
        
        customized_content = template
        for placeholder, value in replacements.items():
            customized_content = customized_content.replace(placeholder, value)
        
        return customized_content
    
    def _build_education_section(self, education: List[Dict]) -> str:
        if not education:
            return "\\textbf{Master in Information Systems}, University of Nouakchott \\hfill Oct 2023 -- Present\\\\[2mm]\n\\textbf{Bachelor of Science in Computer Science}, University of Nouakchott \\hfill Oct 2020 -- Jun 2023\\\\"
        
        section = ""
        for edu in education:
            degree = edu.get('degree', '')
            institution = edu.get('institution', '')
            period = edu.get('period', '')
            section += f"\\textbf{{{degree}}}, {institution} \\hfill {period}\\\\[2mm]\n"
        
        return section.rstrip("\\\\[2mm]\n") + "\\\\"
    
    def _build_experience_section(self, experiences: List[Dict]) -> str:
        if not experiences:
            return ""
        
        section = ""
        for exp in experiences:
            title = exp.get('jobtitle', exp.get('title', ''))
            company = exp.get('company', '')
            period = exp.get('period', '')
            technologies = exp.get('technologies', '')
            responsibilities = exp.get('responsibilities', [])
            
            section += f"\\textbf{{{title}}}, {company} \\hfill {period}\\\\\n"
            if technologies:
                section += f"\\textbf{{Technologies}}: {technologies}\\\\\n"
            
            if responsibilities:
                section += "\\begin{itemize}[noitemsep,topsep=0pt]\n"
                for resp in responsibilities:
                    if resp.strip():
                        section += f"    \\item {resp}\n"
                section += "\\end{itemize}\n\n"
        
        return section
    
    def _build_projects_section(self, projects: List[Dict]) -> str:
        if not projects:
            return ""
        
        section = ""
        for project in projects:
            title = project.get('projecttitle', project.get('title', ''))
            achievement = project.get('achievement/award', project.get('achievement', ''))
            technologies = project.get('technologies', '')
            description = project.get('description', [])
            
            if achievement:
                section += f"\\textbf{{{title}}} \\hfill \\textbf{{{achievement}}}\\\\\n"
            else:
                section += f"\\textbf{{{title}}}\\\\\n"
            
            if technologies:
                section += f"\\textbf{{Technologies}}: {technologies}\\\\\n"
            
            if description:
                section += "\\begin{itemize}[noitemsep,topsep=0pt]\n"
                for desc in description:
                    if desc.strip():
                        section += f"    \\item {desc}\n"
                section += "\\end{itemize}\n"
            
            section += "\\vspace{1cm}\n"
        
        return section
    
    def _build_certifications_section(self, certifications: List[Dict]) -> str:
        if not certifications:
            return "\\textbf{Flutter Bootcamp}, Smart MS SA \\hfill Dec 2023\\\\\n\\textbf{DataCamp Certifications}: Intermediate Git, Intermediate Python for Developers \\hfill 2024-2025\\\\"
        
        section = ""
        for cert in certifications:
            name = cert.get('certificationname', cert.get('name', ''))
            issuer = cert.get('issuer', '')
            date = cert.get('date', '')
            
            section += f"\\textbf{{{name}}}, {issuer} \\hfill {date}\\\\\n"
        
        return section.rstrip("\\\\\n") + "\\\\"
    
    def _build_international_experience(self) -> str:
        return """\\textbf{SalamHack (International Hackathon)} \\hfill 2025\\\\
Team Leader for "Thimar" – AI-powered productivity platform\\\\
\\begin{itemize}[noitemsep,topsep=0pt]
    \\item Led 3-person team to develop task management platform with real-time analytics
    \\item Integrated AI-driven goal recommendations and habit tracking
    \\item Won Supabase Launch Week 14 competition
\\end{itemize}

\\textbf{Ecothon "Green Code of Moscow"} \\hfill 2024\\\\
\\begin{itemize}[noitemsep,topsep=0pt]
    \\item Ranked 16th/29 teams in sustainability competition
    \\item Developed tool for endangered species identification
\\end{itemize}"""
    
    def _prioritize_skills(self, skill_list: List[str], job: Dict) -> List[str]:
        """Put job-relevant skills first"""
        if not skill_list:
            return []
        
        job_text = f"{job['title']} {job['description']} {job['requirements']}".lower()
        prioritized = [skill for skill in skill_list if skill.lower() in job_text]
        remaining = [skill for skill in skill_list if skill.lower() not in job_text]
        
        return (prioritized + remaining)[:8]
    
    def _compile_to_pdf(self, latex_file: Path) -> Optional[str]:
        try:
            original_dir = os.getcwd()
            latex_dir = latex_file.parent
            
            os.chdir(latex_dir)
            
            for i in range(2):
                result = subprocess.run([
                    'pdflatex', 
                    '-interaction=nonstopmode',
                    '-output-directory=.',
                    latex_file.name
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    print(f"LaTeX compilation failed: {result.stderr}")
                    return None
            
            pdf_file = latex_dir / f"{latex_file.stem}.pdf"
            if pdf_file.exists():
                self._cleanup_latex_files(latex_dir, latex_file.stem)
                return str(pdf_file)
            else:
                return None
                
        except subprocess.TimeoutExpired:
            print("LaTeX compilation timed out")
            return None
        except FileNotFoundError:
            print("pdflatex not found")
            return None
        except Exception as e:
            print(f"Error compiling LaTeX: {e}")
            return None
        finally:
            os.chdir(original_dir)
    
    def _cleanup_latex_files(self, latex_dir: Path, stem: str):
        for ext in ['.aux', '.log', '.out', '.fdb_latexmk', '.fls', '.synctex.gz']:
            aux_file = latex_dir / f"{stem}{ext}"
            if aux_file.exists():
                try:
                    aux_file.unlink()
                except:
                    pass
    
    def _create_plain_text_resume(self, job: Dict, job_folder: Path, user_profile: Dict = None) -> str:
        if not user_profile:
            plain_content = f"""
No user profile available. Please set up your profile first.

Target Job: {job['title']} at {job['company']}
Generated: {datetime.now().strftime('%B %d, %Y')}
"""
        else:
            full_name = f"{user_profile.get('firstName', '')} {user_profile.get('lastName', '')}"
            plain_content = f"""
{full_name.upper()}
========================

Email: {user_profile.get('email', '')}
Phone: {user_profile.get('phone', '')}
LinkedIn: {user_profile.get('linkedin', '')}
GitHub: {user_profile.get('github', '')}

PROFESSIONAL SUMMARY:
{user_profile.get('professionalSummary', '')}

Target Job: {job['title']} at {job['company']}
Generated: {datetime.now().strftime('%B %d, %Y')}
"""
        
        plain_file = job_folder / "resume.txt"
        with open(plain_file, 'w', encoding='utf-8') as f:
            f.write(plain_content)
        return str(plain_file)
    
    def _create_plain_text_cover_letter(self, job: Dict, job_folder: Path, user_profile: Dict = None) -> str:
        if not user_profile:
            plain_content = f"""
No user profile available. Please set up your profile first.

Target Job: {job['title']} at {job['company']}
Generated: {datetime.now().strftime('%B %d, %Y')}
"""
        else:
            full_name = f"{user_profile.get('firstName', '')} {user_profile.get('lastName', '')}"
            plain_content = f"""
{full_name}
{user_profile.get('email', '')} | {user_profile.get('phone', '')}
{user_profile.get('location', '')}

{datetime.now().strftime('%B %d, %Y')}

{job['company']}
Hiring Department

Subject: Application for {job['title']} position

Dear Hiring Manager,

I would like to offer my candidacy for the {job['title']} position within your team.

Sincerely,
{full_name}

Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}
"""
        
        plain_file = job_folder / "cover_letter.txt"
        with open(plain_file, 'w', encoding='utf-8') as f:
            f.write(plain_content)
        return str(plain_file)  