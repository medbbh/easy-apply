import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re
import json
import time
import subprocess
import os
import shutil
from dataclasses import dataclass
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote_plus

@dataclass
class JobResult:
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary: Optional[str]
    url: str
    visa_sponsorship: bool
    source: str
    remote_work: bool
    experience_level: str
    tech_stack: str
    folder: str

class TemplateManager:
    def __init__(self):
        self.resume_template_path = Path("resume_template.tex")
        self.cover_letter_template_path = Path("cover_letter_template.txt")
        self.base_output_dir = Path("job_applications")
        
    def load_resume_template(self) -> str:
        """Load LaTeX resume template from external file"""
        if not self.resume_template_path.exists():
            raise FileNotFoundError(f"Resume template not found: {self.resume_template_path}")
        
        with open(self.resume_template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_cover_letter_template(self) -> str:
        """Load cover letter template from external file"""
        if not self.cover_letter_template_path.exists():
            raise FileNotFoundError(f"Cover letter template not found: {self.cover_letter_template_path}")
        
        with open(self.cover_letter_template_path, 'r', encoding='utf-8') as f:
            return f.read()
        
    def clear_job_applications_folder(self):
        """Clear existing job application folders before new search"""
        if self.base_output_dir.exists():
            shutil.rmtree(self.base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)

class ResumeGenerator:
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
        
    def get_custom_summary(self, job: Dict) -> str:
        """Generate custom summary based on job type"""
        title_lower = job['title'].lower()
        
        if any(term in title_lower for term in ['frontend', 'front-end', 'react', 'angular', 'vue']):
            return "Frontend-focused Full Stack Developer with expertise in React, Angular, and modern JavaScript frameworks."
        elif any(term in title_lower for term in ['backend', 'back-end', 'api', 'server']):
            return "Backend-focused Full Stack Developer specializing in Python/Django and scalable API development."
        elif any(term in title_lower for term in ['fullstack', 'full-stack', 'full stack']):
            return "Experienced Full Stack Developer with comprehensive expertise in both frontend and backend technologies."
        elif any(term in title_lower for term in ['data', 'analyst', 'analytics']):
            return "Analytical professional with strong technical background and expertise in data-driven decision making."
        elif any(term in title_lower for term in ['mobile', 'ios', 'android', 'flutter', 'react native']):
            return "Mobile-focused developer with experience in cross-platform development and modern mobile technologies."
        elif any(term in title_lower for term in ['marketing', 'sales', 'business']):
            return "Business professional with strong analytical skills and proven track record in growth initiatives."
        elif any(term in title_lower for term in ['design', 'creative', 'ui', 'ux']):
            return "Creative professional with technical background and user-centered design approach."
        else:
            return "Versatile technology professional with comprehensive development skills and proven international collaboration experience."
    
    def get_prioritized_skills(self, job: Dict, category: str) -> str:
        """Get prioritized skills for specific categories based on job requirements"""
        
        job_text = f"{job['title']} {job['description']} {job['requirements']}".lower()
        
        skill_categories = {
            'programming': ['Python', 'JavaScript', 'TypeScript', 'Java', 'PHP', 'C++', 'C#', 'SQL', 'HTML5', 'CSS3'],
            'frameworks': ['React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Node.js', 'Express', 'Laravel', 'Spring Boot'],
            'databases': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'SQLite', 'Firebase'],
            'tools': ['Git', 'Docker', 'AWS', 'Azure', 'Linux', 'Postman', 'Jira', 'VS Code', 'Figma']
        }
        
        if category not in skill_categories:
            return "Various professional tools and technologies"
        
        skills = skill_categories[category]
        prioritized = []
        remaining = []
        
        # Prioritize skills mentioned in job
        for skill in skills:
            if skill.lower() in job_text:
                prioritized.append(skill)
            else:
                remaining.append(skill)
        
        # Combine prioritized + remaining, limit to 6-8 items
        final_skills = prioritized + remaining
        return ', '.join(final_skills[:8])
    
    def generate_resume(self, job: Dict, job_folder: Path) -> str:
        """Generate customized resume using external template"""
        
        # Load template
        template_content = self.template_manager.load_resume_template()
        
        # Replace placeholders with job-specific content
        replacements = {
            '{TARGET_POSITION}': job['title'],
            '{TARGET_COMPANY}': job['company'],
            '{TARGET_LOCATION}': job['location'],
            '{PROFESSIONAL_SUMMARY}': self.get_custom_summary(job),
            '{PROGRAMMING_SKILLS}': self.get_prioritized_skills(job, 'programming'),
            '{FRAMEWORK_SKILLS}': self.get_prioritized_skills(job, 'frameworks'),
            '{DATABASE_SKILLS}': self.get_prioritized_skills(job, 'databases'),
            '{TOOL_SKILLS}': self.get_prioritized_skills(job, 'tools'),
            '{GENERATION_DATE}': datetime.now().strftime('%B %d, %Y at %H:%M'),
            '{JOB_SOURCE}': job['source']
        }
        
        # Apply all replacements
        customized_content = template_content
        for placeholder, value in replacements.items():
            customized_content = customized_content.replace(placeholder, value)
        
        # Save LaTeX file
        resume_file = job_folder / "resume.tex"
        with open(resume_file, 'w', encoding='utf-8') as f:
            f.write(customized_content)
        
        # Compile to PDF
        pdf_path = self.compile_to_pdf(resume_file)
        
        # Create plain text backup
        self.create_plain_text_resume(job, job_folder)
        
        return pdf_path if pdf_path else str(resume_file)
    
    def compile_to_pdf(self, latex_file: Path) -> Optional[str]:
        """Compile LaTeX to PDF and save in job folder"""
        try:
            original_dir = os.getcwd()
            latex_dir = latex_file.parent
            
            os.chdir(latex_dir)
            
            # Compile LaTeX twice for proper cross-references
            for i in range(2):
                result = subprocess.run([
                    'pdflatex', 
                    '-interaction=nonstopmode',
                    '-output-directory=.',
                    latex_file.name
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    return None
            
            # Check if PDF was created
            pdf_file = latex_dir / f"{latex_file.stem}.pdf"
            if pdf_file.exists():
                # Clean up auxiliary files
                for ext in ['.aux', '.log', '.out', '.fdb_latexmk', '.fls', '.synctex.gz']:
                    aux_file = latex_dir / f"{latex_file.stem}{ext}"
                    if aux_file.exists():
                        aux_file.unlink()
                
                return str(pdf_file)
            else:
                return None
                
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            return None
        except Exception as e:
            return None
        finally:
            os.chdir(original_dir)
    
    def create_plain_text_resume(self, job: Dict, job_folder: Path):
        """Create plain text version as backup"""
        
        plain_content = f"""
M'HAMED BABAH - SOFTWARE DEVELOPER & IT PROFESSIONAL
=====================================================

TARGET POSITION: {job['title']}
TARGET COMPANY: {job['company']}
TARGET LOCATION: {job['location']}
VISA STATUS: Seeking Work Permit Sponsorship

CONTACT INFORMATION:
Email: mhamed.bbh01@gmail.com
Phone: +222 34503710
LinkedIn: linkedin.com/in/mhamed-elbah-6a954b211
GitHub: github.com/medbbh
Location: Nouakchott, Mauritania

PROFESSIONAL SUMMARY:
{self.get_custom_summary(job)} Currently pursuing Master's in Information Systems with proven track record in international competitions. Seeking visa sponsorship to contribute to innovative teams.

TECHNICAL SKILLS:
Programming: {self.get_prioritized_skills(job, 'programming')}
Frameworks: {self.get_prioritized_skills(job, 'frameworks')}
Databases: {self.get_prioritized_skills(job, 'databases')}
Tools: {self.get_prioritized_skills(job, 'tools')}

KEY ACHIEVEMENTS:
• WINNER: Supabase Launch Week 14 Competition (Thimar Platform)
• WINNER: SalamHack International Hackathon 2025 (Team Leader)
• Ranked 16th/29: Ecothon "Green Code of Moscow" 2024
• Led international teams to competition victories

PROFESSIONAL EXPERIENCE:

Head of IT | NJ Consulting | Present
• Lead technical infrastructure and strategic technology decisions
• Manage full-stack development projects with international clients
• Implement security protocols and best practices

Software Developer Intern | Next Technology | Jul 2023 - Present
• Developed REST APIs for e-commerce platform
• Integrated Stripe payment processing
• Implemented JWT authentication systems

EDUCATION:
Master in Information Systems | University of Nouakchott | Oct 2023 - Present
Bachelor of Science in Computer Science | University of Nouakchott | Oct 2020 - Jun 2023

INTERNATIONAL READINESS:
✓ Strong English communication for global collaboration
✓ Experience leading diverse, international teams
✓ Ready to relocate with visa sponsorship
✓ Available to start immediately upon visa approval

Generated: {datetime.now().strftime('%B %d, %Y')}
Customized for: {job['company']} - {job['title']}
Source: {job['source']}
"""
        
        plain_file = job_folder / "resume.txt"
        with open(plain_file, 'w', encoding='utf-8') as f:
            f.write(plain_content)

class CoverLetterGenerator:
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
    
    def get_custom_paragraph(self, job: Dict) -> str:
        """Generate custom paragraph based on job type"""
        title_lower = job['title'].lower()
        
        if any(term in title_lower for term in ['developer', 'engineer', 'programmer']):
            return "My technical expertise includes hands-on experience with modern development frameworks and best practices. I have successfully delivered multiple projects involving API development, database design, and user interface implementation, which aligns perfectly with the technical requirements of this role."
        elif any(term in title_lower for term in ['analyst', 'data', 'research']):
            return "My analytical background includes extensive experience with data analysis, research methodologies, and statistical interpretation. I have successfully applied these skills in competitive environments and real-world projects, demonstrating my ability to extract insights and drive data-informed decisions."
        elif any(term in title_lower for term in ['marketing', 'sales', 'business']):
            return "My business acumen is complemented by my technical background, providing a unique perspective on market dynamics and customer needs. I have successfully led teams and projects that required both strategic thinking and practical execution, skills that are directly applicable to this role."
        elif any(term in title_lower for term in ['design', 'creative', 'ui', 'ux']):
            return "My design sensibility is enhanced by my technical understanding, allowing me to create solutions that are both aesthetically pleasing and functionally robust. I have experience in user-centered design approaches and understand the importance of balancing creativity with usability."
        else:
            return "My diverse skill set and international experience have prepared me to tackle complex challenges and adapt to dynamic work environments. I am particularly excited about the opportunity to bring fresh perspectives and innovative approaches to your team."
    
    def generate_cover_letter(self, job: Dict, job_folder: Path):
        """Generate customized cover letter using external template"""
        
        # Load template
        template_content = self.template_manager.load_cover_letter_template()
        
        # Replace placeholders with job-specific content
        replacements = {
            '{TARGET_POSITION}': job['title'],
            '{TARGET_COMPANY}': job['company'],
            '{TARGET_LOCATION}': job['location'],
            '{JOB_SOURCE}': job['source'],
            '{JOB_REQUIREMENTS}': job['requirements'],
            '{JOB_URL}': job['url'],
            '{EXPERIENCE_LEVEL}': job['experience_level'],
            '{APPLICATION_DATE}': datetime.now().strftime('%B %d, %Y'),
            '{CUSTOM_PARAGRAPH}': self.get_custom_paragraph(job)
        }
        
        # Apply all replacements
        customized_content = template_content
        for placeholder, value in replacements.items():
            customized_content = customized_content.replace(placeholder, value)
        
        # Save cover letter
        cover_letter_file = job_folder / "cover_letter.txt"
        with open(cover_letter_file, 'w', encoding='utf-8') as f:
            f.write(customized_content)

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.template_manager = TemplateManager()
        self.resume_generator = ResumeGenerator(self.template_manager)
        self.cover_letter_generator = CoverLetterGenerator(self.template_manager)
    
    def search_and_prepare(self, keywords: List[str]) -> List[JobResult]:
        """Main method: search jobs and prepare applications with PDFs"""
        
        # Clear previous job applications and check LaTeX
        self.template_manager.clear_job_applications_folder()
        
        all_jobs = []
        
        # Create search query from keywords
        search_query = ' '.join(keywords)
        
        # Scrape multiple sources (keeping all existing scraping methods)
        all_jobs.extend(self._scrape_indeed_comprehensive(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_monster(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_ziprecruiter(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_linkedin_jobs(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_careerbuilder(search_query))
        
        # Remove duplicates
        unique_jobs = self._remove_duplicates(all_jobs)
        
        # Prepare applications for each job
        results = []
        pdf_count = 0
        
        for job in unique_jobs:
            try:
                folder_name, pdf_generated = self._prepare_application(job)
                if pdf_generated:
                    pdf_count += 1
                    
                result = JobResult(
                    title=job['title'],
                    company=job['company'],
                    location=job['location'],
                    description=job['description'],
                    requirements=job['requirements'],
                    salary=job['salary'],
                    url=job['url'],
                    visa_sponsorship=job['visa_sponsorship'],
                    source=job['source'],
                    remote_work=job['remote_work'],
                    experience_level=job['experience_level'],
                    tech_stack=job['tech_stack'],
                    folder=folder_name
                )
                results.append(result)
            except Exception as e:
                continue
        
        print(f"\n🎯 Generated {len(results)} job applications")
        if self.template_manager.pdf_generator.latex_available:
            print(f"📄 {pdf_count} PDFs successfully created")
        else:
            print("⚠️ PDFs not generated - LaTeX not installed")
            
        return results
    
    def _prepare_application(self, job: Dict) -> tuple[str, bool]:
        """Prepare application folder with PDF resume and cover letter"""
        # Create folder
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', job['company'])
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job['title'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        folder_name = f"{safe_company}_{safe_title}_{timestamp}"
        job_folder = self.template_manager.base_output_dir / folder_name
        job_folder.mkdir(exist_ok=True)
        
        # Save job info
        with open(job_folder / "job_info.json", 'w', encoding='utf-8') as f:
            json.dump(job, f, indent=2, ensure_ascii=False)
        
        # Generate resume PDF using external template
        resume_pdf = self.resume_generator.generate_resume(job, job_folder)
        
        # Generate cover letter PDF using external template
        cover_letter_pdf = self.cover_letter_generator.generate_cover_letter(job, job_folder)
        
        pdf_generated = resume_pdf or cover_letter_pdf
        
        return folder_name, pdf_generated
    
    def _scrape_indeed_comprehensive(self, search_query: str) -> List[Dict]:
        """Comprehensive Indeed scraping for ANY job type"""
        jobs = []
        
        try:
            # Multiple Indeed searches with different parameters
            base_urls = [
                f"https://www.indeed.com/jobs?q={quote_plus(search_query)}&sort=date",
                f"https://www.indeed.com/jobs?q={quote_plus(search_query)}&l=&sort=date&fromage=7",
                f"https://www.indeed.com/jobs?q={quote_plus(search_query)}&l=United+States&sort=date",
            ]
            
            for url in base_urls:
                try:
                    response = self.session.get(url, timeout=15)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Multiple selectors for Indeed's changing structure
                    job_containers = (
                        soup.find_all('div', class_='job_seen_beacon') or
                        soup.find_all('div', class_='slider_container') or
                        soup.find_all('div', class_='jobsearch-SerpJobCard') or
                        soup.find_all('a', {'data-jk': True}) or
                        soup.find_all('div', {'data-jk': True})
                    )
                    
                    for container in job_containers[:12]:  # Get up to 12 jobs per search
                        try:
                            job = self._extract_indeed_job(container)
                            if job:
                                jobs.append(job)
                        except:
                            continue
                            
                    time.sleep(2)  # Rate limiting
                    
                except:
                    continue
                    
        except:
            pass
        
        return jobs
    
    def _extract_indeed_job(self, container) -> Optional[Dict]:
        """Extract job details from Indeed container"""
        try:
            # Title extraction with multiple selectors
            title_elem = (
                container.find('h2', class_='jobTitle') or
                container.find('span', {'title': True}) or
                container.find('a', {'data-jk': True}) or
                container.find('h2') or
                container.find('a', class_='jobTitle-color-purple')
            )
            
            if not title_elem:
                return None
                
            title = title_elem.get('title') or title_elem.get_text(strip=True)
            if not title or len(title) < 3:
                return None
            
            # Company extraction
            company_elem = (
                container.find('span', class_='companyName') or
                container.find('a', {'data-testid': 'company-name'}) or
                container.find('div', class_='companyName') or
                container.find('span', class_='company')
            )
            
            if not company_elem:
                return None
                
            company = company_elem.get_text(strip=True)
            
            # Location extraction
            location_elem = (
                container.find('div', class_='companyLocation') or
                container.find('div', {'data-testid': 'job-location'}) or
                container.find('span', class_='location')
            )
            
            location = location_elem.get_text(strip=True) if location_elem else "Various Locations"
            
            # URL extraction
            link_elem = container.find('a', {'data-jk': True}) or title_elem
            if link_elem and link_elem.get('href'):
                job_url = urljoin("https://www.indeed.com", link_elem['href'])
            elif link_elem and link_elem.get('data-jk'):
                job_url = f"https://www.indeed.com/viewjob?jk={link_elem['data-jk']}"
            else:
                job_url = f"https://www.indeed.com/jobs?q={quote_plus(title)}"
            
            # Salary extraction
            salary_elem = (
                container.find('span', class_='salary-snippet') or
                container.find('div', class_='salary-snippet-container') or
                container.find('span', class_='estimated-salary')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else "Competitive"
            
            # Description extraction
            snippet_elem = (
                container.find('div', class_='job-snippet') or
                container.find('span', class_='summary') or
                container.find('div', class_='summary')
            )
            description = snippet_elem.get_text(strip=True) if snippet_elem else f"{title} position at {company} in {location}."
            
            # Job analysis
            full_text = f"{title} {company} {description} {location}".lower()
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'requirements': self._extract_skills_from_text(full_text),
                'salary': salary,
                'url': job_url,
                'visa_sponsorship': self._check_visa_friendly(full_text),
                'source': 'Indeed',
                'remote_work': 'remote' in full_text or 'work from home' in full_text,
                'experience_level': self._get_experience_level(title),
                'tech_stack': self._extract_tech_from_text(full_text)
            }
            
        except:
            return None
    
    def _scrape_monster(self, search_query: str) -> List[Dict]:
        """Scrape Monster.com for jobs"""
        jobs = []
        
        try:
            url = f"https://www.monster.com/jobs/search?q={quote_plus(search_query)}&where=__2C-US&page=1"
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Monster job selectors
            job_containers = (
                soup.find_all('section', class_='card-content') or
                soup.find_all('div', class_='flex-row') or
                soup.find_all('article')
            )
            
            for container in job_containers[:10]:
                try:
                    title_elem = container.find('h2') or container.find('a', class_='title')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    company_elem = container.find('div', class_='company') or container.find('span', class_='company')
                    company = company_elem.get_text(strip=True) if company_elem else "Various Companies"
                    
                    location_elem = container.find('div', class_='location') or container.find('span', class_='location')
                    location = location_elem.get_text(strip=True) if location_elem else "Various Locations"
                    
                    # URL
                    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                    job_url = urljoin("https://www.monster.com", link_elem['href']) if link_elem and link_elem.get('href') else f"https://www.monster.com/jobs/search?q={quote_plus(search_query)}"
                    
                    description = f"{title} position at {company} in {location}. Apply through Monster.com for full details."
                    full_text = f"{title} {company} {description} {location}".lower()
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'requirements': self._extract_skills_from_text(full_text),
                        'salary': "Competitive",
                        'url': job_url,
                        'visa_sponsorship': self._check_visa_friendly(full_text),
                        'source': 'Monster',
                        'remote_work': 'remote' in full_text,
                        'experience_level': self._get_experience_level(title),
                        'tech_stack': self._extract_tech_from_text(full_text)
                    })
                    
                except:
                    continue
                    
        except:
            pass
        
        return jobs
    
    def _scrape_ziprecruiter(self, search_query: str) -> List[Dict]:
        """Scrape ZipRecruiter for jobs"""
        jobs = []
        
        try:
            url = f"https://www.ziprecruiter.com/jobs-search?search={quote_plus(search_query)}&location="
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ZipRecruiter selectors
            job_containers = (
                soup.find_all('div', class_='job_content') or
                soup.find_all('article', class_='job_result') or
                soup.find_all('div', {'data-testid': 'job-list-item'})
            )
            
            for container in job_containers[:8]:
                try:
                    title_elem = container.find('h2') or container.find('a', class_='job_link')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    company_elem = container.find('a', class_='company_name') or container.find('span', class_='company')
                    company = company_elem.get_text(strip=True) if company_elem else "Various Companies"
                    
                    location_elem = container.find('span', class_='location') or container.find('div', class_='location')
                    location = location_elem.get_text(strip=True) if location_elem else "Various Locations"
                    
                    # URL
                    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                    job_url = urljoin("https://www.ziprecruiter.com", link_elem['href']) if link_elem and link_elem.get('href') else f"https://www.ziprecruiter.com/jobs-search?search={quote_plus(search_query)}"
                    
                    # Salary
                    salary_elem = container.find('span', class_='salary') or container.find('div', class_='salary')
                    salary = salary_elem.get_text(strip=True) if salary_elem else "Competitive"
                    
                    description = f"{title} opportunity at {company} in {location}. Full job details available on ZipRecruiter."
                    full_text = f"{title} {company} {description} {location}".lower()
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'requirements': self._extract_skills_from_text(full_text),
                        'salary': salary,
                        'url': job_url,
                        'visa_sponsorship': self._check_visa_friendly(full_text),
                        'source': 'ZipRecruiter',
                        'remote_work': 'remote' in full_text,
                        'experience_level': self._get_experience_level(title),
                        'tech_stack': self._extract_tech_from_text(full_text)
                    })
                    
                except:
                    continue
                    
        except:
            pass
        
        return jobs
    
    def _scrape_linkedin_jobs(self, search_query: str) -> List[Dict]:
        """Fixed LinkedIn Jobs scraping with working URLs"""
        jobs = []
        
        try:
            # Use LinkedIn's public job search with better URL construction
            encoded_query = quote_plus(search_query)
            
            # Multiple LinkedIn search strategies
            search_urls = [
                f"https://www.linkedin.com/jobs/search?keywords={encoded_query}&location=&geoId=&f_TPR=r604800",
                f"https://www.linkedin.com/jobs/search?keywords={encoded_query}&location=United%20States&f_TPR=r604800",
                f"https://www.linkedin.com/jobs/search?keywords={encoded_query}&f_E=2%2C3&f_TPR=r604800"  # Entry/Associate level
            ]
            
            for search_url in search_urls[:2]:  # Try first 2 URLs
                try:
                    # Use different headers for LinkedIn
                    linkedin_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                    
                    response = requests.get(search_url, headers=linkedin_headers, timeout=15)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Multiple LinkedIn selectors (they change frequently)
                    job_containers = (
                        soup.find_all('div', class_='base-card') or
                        soup.find_all('div', class_='base-search-card') or
                        soup.find_all('li', class_='result-card') or
                        soup.find_all('div', {'data-entity-urn': True}) or
                        soup.find_all('article', class_='job-card') or
                        soup.find_all('div', class_='job-card-container')
                    )
                    
                    for container in job_containers[:8]:  # Limit to 8 jobs per URL
                        try:
                            job = self._extract_linkedin_job(container, encoded_query)
                            if job:
                                jobs.append(job)
                        except:
                            continue
                    
                    time.sleep(3)  # Longer delay for LinkedIn
                    
                except:
                    continue
                    
        except:
            pass
        
        # If no jobs found from scraping, create fallback jobs with working search URLs
        if len(jobs) == 0:
            jobs.extend(self._create_linkedin_fallback_jobs(search_query))
        
        return jobs
    
    def _extract_linkedin_job(self, container, encoded_query: str) -> Optional[Dict]:
        """Extract job details from LinkedIn container with better URL handling"""
        try:
            # Title extraction with multiple selectors
            title_elem = (
                container.find('h3', class_='base-search-card__title') or
                container.find('a', class_='result-card__title-link') or
                container.find('h3') or
                container.find('a', {'data-tracking-will-navigate': True}) or
                container.find('span', class_='sr-only')
            )
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 3:
                return None
            
            # Company extraction
            company_elem = (
                container.find('h4', class_='base-search-card__subtitle') or
                container.find('a', class_='result-card__subtitle-link') or
                container.find('h4') or
                container.find('span', class_='job-result-card__company-name')
            )
            
            company = company_elem.get_text(strip=True) if company_elem else "LinkedIn Company"
            
            # Location extraction
            location_elem = (
                container.find('span', class_='job-result-card__location') or
                container.find('span', class_='result-card__location') or
                container.find('div', class_='base-search-card__metadata')
            )
            
            location = location_elem.get_text(strip=True) if location_elem else "Various Locations"
            
            # Better URL construction strategy
            job_url = self._construct_linkedin_job_url(container, title, company, encoded_query)
            
            # Description
            description = f"Professional opportunity: {title} at {company}. This position offers excellent career growth potential. View full details and apply through LinkedIn's platform."
            
            full_text = f"{title} {company} {description} {location}".lower()
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'requirements': self._extract_skills_from_text(full_text),
                'salary': "Competitive",
                'url': job_url,
                'visa_sponsorship': self._check_visa_friendly(full_text),
                'source': 'LinkedIn',
                'remote_work': 'remote' in full_text,
                'experience_level': self._get_experience_level(title),
                'tech_stack': self._extract_tech_from_text(full_text)
            }
            
        except:
            return None
    
    def _construct_linkedin_job_url(self, container, title: str, company: str, encoded_query: str) -> str:
        """Construct working LinkedIn job URL with multiple strategies"""
        
        # Strategy 1: Try to extract job ID from data attributes
        job_id = None
        
        # Look for job ID in various attributes
        for attr in ['data-entity-urn', 'data-job-id', 'data-tracking-will-navigate']:
            if container.get(attr):
                # Extract job ID from URN or URL
                attr_value = container[attr]
                job_id_match = re.search(r'(\d{10,})', attr_value)
                if job_id_match:
                    job_id = job_id_match.group(1)
                    break
        
        # Strategy 2: Look for job ID in href attributes
        if not job_id:
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                job_id_match = re.search(r'/jobs/view/(\d+)', href)
                if job_id_match:
                    job_id = job_id_match.group(1)
        
        # Strategy 3: Construct URL with job ID if found
        if job_id:
            return f"https://www.linkedin.com/jobs/view/{job_id}"
        
        # Strategy 4: Fallback to search URL with specific terms
        search_terms = f"{title} {company}".replace(' ', '%20')
        return f"https://www.linkedin.com/jobs/search?keywords={search_terms}&location=&geoId="
    
    def _create_linkedin_fallback_jobs(self, search_query: str) -> List[Dict]:
        """Create fallback LinkedIn jobs with working search URLs when scraping fails"""
        
        # Common job variations based on search query
        job_variations = []
        
        query_lower = search_query.lower()
        
        if 'analyst' in query_lower:
            job_variations = [
                ("Data Analyst", "Tech Company"),
                ("Business Analyst", "Consulting Firm"), 
                ("Research Analyst", "Financial Services"),
                ("Marketing Analyst", "Marketing Agency")
            ]
        elif 'developer' in query_lower or 'engineer' in query_lower:
            job_variations = [
                ("Software Developer", "Technology Company"),
                ("Frontend Developer", "Startup"),
                ("Backend Engineer", "Software Company"),
                ("Full Stack Developer", "Tech Startup")
            ]
        elif 'marketing' in query_lower:
            job_variations = [
                ("Marketing Coordinator", "Marketing Agency"),
                ("Digital Marketing Specialist", "E-commerce Company"),
                ("Marketing Manager", "Tech Company"),
                ("Content Marketing Specialist", "Media Company")
            ]
        elif 'sales' in query_lower:
            job_variations = [
                ("Sales Representative", "Software Company"),
                ("Sales Development Representative", "SaaS Company"),
                ("Account Executive", "Technology Firm"),
                ("Business Development Associate", "Startup")
            ]
        elif 'customer' in query_lower or 'support' in query_lower:
            job_variations = [
                ("Customer Success Manager", "SaaS Company"),
                ("Customer Support Specialist", "Tech Company"),
                ("Client Services Representative", "Service Company"),
                ("Technical Support Engineer", "Software Company")
            ]
        else:
            # Generic fallback based on search terms
            job_variations = [
                (f"{search_query.title()} Specialist", "Professional Services"),
                (f"{search_query.title()} Coordinator", "Growing Company"),
                (f"{search_query.title()} Associate", "Industry Leader"),
                (f"Junior {search_query.title()}", "Dynamic Team")
            ]
        
        fallback_jobs = []
        
        for i, (job_title, company_type) in enumerate(job_variations[:4]):
            # Create search URL that will definitely work
            search_url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(job_title)}&location=&geoId="
            
            fallback_jobs.append({
                'title': job_title,
                'company': f"{company_type} (LinkedIn Search)",
                'location': "Multiple Locations",
                'description': f"Browse {job_title} opportunities on LinkedIn. This search will show you current openings that match your criteria. LinkedIn has thousands of {job_title.lower()} positions from companies worldwide.",
                'requirements': self._extract_skills_from_text(job_title.lower()),
                'salary': "Competitive",
                'url': search_url,
                'visa_sponsorship': True,
                'source': 'LinkedIn',
                'remote_work': 'remote' in search_query.lower(),
                'experience_level': self._get_experience_level(job_title),
                'tech_stack': self._extract_tech_from_text(job_title.lower())
            })
        
        return fallback_jobs
    
    def _scrape_careerbuilder(self, search_query: str) -> List[Dict]:
        """Scrape CareerBuilder for jobs"""
        jobs = []
        
        try:
            url = f"https://www.careerbuilder.com/jobs?keywords={quote_plus(search_query)}&location="
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # CareerBuilder selectors
            job_containers = (
                soup.find_all('div', class_='data-results-content') or
                soup.find_all('div', class_='job-listing') or
                soup.find_all('article')
            )
            
            for container in job_containers[:6]:
                try:
                    title_elem = container.find('h2') or container.find('a', class_='data-results-content-parent')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    company_elem = container.find('div', class_='data-details') or container.find('span', class_='company')
                    company = company_elem.get_text(strip=True) if company_elem else "Various Companies"
                    
                    location_elem = container.find('div', class_='data-details')
                    location = "Various Locations"  # CareerBuilder location is complex to extract
                    
                    # URL
                    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                    job_url = urljoin("https://www.careerbuilder.com", link_elem['href']) if link_elem and link_elem.get('href') else f"https://www.careerbuilder.com/jobs?keywords={quote_plus(search_query)}"
                    
                    description = f"{title} role at {company}. Explore full opportunity details on CareerBuilder."
                    full_text = f"{title} {company} {description} {location}".lower()
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'requirements': self._extract_skills_from_text(full_text),
                        'salary': "Competitive",
                        'url': job_url,
                        'visa_sponsorship': self._check_visa_friendly(full_text),
                        'source': 'CareerBuilder',
                        'remote_work': 'remote' in full_text,
                        'experience_level': self._get_experience_level(title),
                        'tech_stack': self._extract_tech_from_text(full_text)
                    })
                    
                except:
                    continue
                    
        except:
            pass
        
        return jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job['title'].lower()}_{job['company'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _check_visa_friendly(self, text: str) -> bool:
        """Check if job is visa-friendly"""
        visa_indicators = [
            'visa sponsorship', 'h1b', 'work permit', 'immigration support',
            'international candidates', 'work authorization', 'sponsor visa',
            'remote', 'global', 'worldwide', 'international'
        ]
        return any(indicator in text.lower() for indicator in visa_indicators)
    
    def _extract_skills_from_text(self, text: str) -> str:
        """Extract skills from job text"""
        all_skills = [
            'python', 'javascript', 'java', 'react', 'django', 'node.js', 'sql', 'html', 'css',
            'git', 'docker', 'aws', 'azure', 'kubernetes', 'typescript', 'angular', 'vue',
            'communication', 'leadership', 'management', 'analysis', 'excel', 'powerpoint',
            'marketing', 'sales', 'customer service', 'design', 'photoshop', 'illustrator',
            'accounting', 'finance', 'project management', 'agile', 'scrum'
        ]
        
        found_skills = [skill.title() for skill in all_skills if skill in text.lower()]
        return ', '.join(found_skills[:6]) if found_skills else "Various professional skills"
    
    def _extract_tech_from_text(self, text: str) -> str:
        """Extract tech skills specifically"""
        tech_skills = [
            'python', 'javascript', 'java', 'react', 'django', 'node.js', 'sql', 'html', 'css',
            'git', 'docker', 'aws', 'azure', 'typescript', 'angular', 'vue', 'php', 'c++', 'c#'
        ]
        
        found_tech = [tech.title() for tech in tech_skills if tech in text.lower()]
        return ', '.join(found_tech[:4]) if found_tech else "Professional tools"
    
    def _get_experience_level(self, title: str) -> str:
        """Determine experience level"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['senior', 'sr', 'lead', 'principal', 'manager', 'director']):
            return 'Senior'
        elif any(word in title_lower for word in ['junior', 'jr', 'entry', 'graduate', 'intern', 'associate']):
            return 'Junior'
        else:
            return 'Mid-level'

if __name__ == "__main__":
    scraper = JobScraper()
    results = scraper.search_and_prepare(['data analyst'])
    for result in results:
        print(f"Generated application for {result.company} - {result.title}")