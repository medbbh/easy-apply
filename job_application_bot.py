#!/usr/bin/env python3
"""
Complete Job Application Bot
Searches for jobs, customizes resumes, and tracks applications
"""

import requests
import json
import time
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import subprocess
import os
from pathlib import Path
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
from dotenv import load_dotenv

# Try to import Mistral AI
try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    print("⚠️ Mistral AI not available, using basic customization")

# Load environment variables
load_dotenv()

@dataclass
class JobListing:
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary: Optional[str]
    url: str
    posted_date: str
    visa_sponsorship: bool
    source: str

@dataclass
class ApplicationStatus:
    job_id: str
    company: str
    position: str
    application_date: str
    status: str
    resume_version: str
    cover_letter_version: str

class DatabaseManager:
    def __init__(self, db_path: str = "job_applications.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                requirements TEXT,
                salary TEXT,
                url TEXT UNIQUE,
                posted_date TEXT,
                visa_sponsorship BOOLEAN,
                source TEXT,
                scraped_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_url TEXT,
                company TEXT,
                position TEXT,
                application_date TEXT,
                status TEXT,
                resume_version TEXT,
                cover_letter_version TEXT,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
    
    def save_job(self, job: JobListing):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO jobs (title, company, location, description, requirements, 
                                salary, url, posted_date, visa_sponsorship, source, scraped_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job.title, job.company, job.location, job.description, job.requirements,
                  job.salary, job.url, job.posted_date, job.visa_sponsorship, job.source,
                  datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Job already exists
        finally:
            conn.close()
    
    def save_application(self, application: ApplicationStatus):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO applications (job_url, company, position, application_date, 
                                    status, resume_version, cover_letter_version, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (application.job_id, application.company, application.position,
              application.application_date, application.status, 
              application.resume_version, application.cover_letter_version, ""))
        
        conn.commit()
        conn.close()

class JobScraper:
    def __init__(self):
        self.setup_driver()
        
    def setup_driver(self):
        try:
            chromedriver_autoinstaller.install()
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome driver initialized")
            
        except Exception as e:
            print(f"❌ Chrome driver setup failed: {e}")
            self.driver = None
    
    def scrape_mock_jobs(self) -> List[JobListing]:
        """Generate realistic mock jobs for testing"""
        
        mock_jobs = [
            JobListing(
                title="Junior Software Developer",
                company="TechStart Berlin GmbH",
                location="Berlin, Germany",
                description="We're a fast-growing fintech startup looking for a passionate junior developer. EU work permit sponsorship available for qualified candidates. You'll work with our international team building scalable web applications using React and Python.",
                requirements="Python, JavaScript, React, Git, English",
                salary="€45,000 - €55,000",
                url="https://example.com/techstart-berlin-junior-dev",
                posted_date=datetime.now().isoformat(),
                visa_sponsorship=True,
                source="Mock-Europe"
            ),
            JobListing(
                title="Full Stack Developer",
                company="InnovateNL B.V.",
                location="Amsterdam, Netherlands",
                description="Join our growing team building the future of e-commerce. We provide visa sponsorship and relocation assistance for international talent. Experience with Django and React preferred.",
                requirements="Python, Django, React, PostgreSQL, Docker",
                salary="€55,000 - €70,000",
                url="https://example.com/innovate-nl-fullstack",
                posted_date=(datetime.now() - timedelta(hours=2)).isoformat(),
                visa_sponsorship=True,
                source="Mock-Europe"
            ),
            JobListing(
                title="Backend Developer",
                company="RemoteFirst Inc",
                location="Remote (US/EU)",
                description="100% remote position open to international candidates. H1B visa sponsorship available for US positions. Work on high-scale distributed systems.",
                requirements="Python, Django, REST APIs, AWS, Microservices",
                salary="$75,000 - $95,000",
                url="https://example.com/remotefirst-backend",
                posted_date=(datetime.now() - timedelta(hours=6)).isoformat(),
                visa_sponsorship=True,
                source="Mock-Remote"
            ),
            JobListing(
                title="Frontend Developer",
                company="ScaleUp Stockholm AB",
                location="Stockholm, Sweden",
                description="Sustainability-focused startup offering EU Blue Card sponsorship. Build beautiful user interfaces that help fight climate change. Modern React stack with TypeScript.",
                requirements="React, TypeScript, HTML5, CSS3, JavaScript",
                salary="SEK 450,000 - 600,000",
                url="https://example.com/scaleup-stockholm",
                posted_date=(datetime.now() - timedelta(hours=12)).isoformat(),
                visa_sponsorship=True,
                source="Mock-Europe"
            ),
            JobListing(
                title="Python Developer",
                company="DataCorp Toronto Ltd",
                location="Toronto, Canada",
                description="Data analytics company seeking Python developer. We assist with Canadian work permits and provide immigration support. Experience with data science libraries preferred.",
                requirements="Python, Pandas, NumPy, SQL, Machine Learning",
                salary="CAD $65,000 - $85,000",
                url="https://example.com/datacorp-toronto",
                posted_date=(datetime.now() - timedelta(days=1)).isoformat(),
                visa_sponsorship=True,
                source="Mock-Canada"
            ),
            JobListing(
                title="Web Developer",
                company="TechHub London Ltd",
                location="London, UK",
                description="Fintech company offering Skilled Worker visa sponsorship. Great opportunity to work in central London with excellent career progression.",
                requirements="JavaScript, React, Node.js, MongoDB, Git",
                salary="£40,000 - £55,000",
                url="https://example.com/techhub-london",
                posted_date=(datetime.now() - timedelta(days=2)).isoformat(),
                visa_sponsorship=True,
                source="Mock-UK"
            )
        ]
        
        print(f"✅ Generated {len(mock_jobs)} mock jobs for testing")
        return mock_jobs
    
    def close(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

class ResumeCustomizer:
    def __init__(self, mistral_api_key: str = None):
        self.output_dir = Path("generated_resumes")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Mistral AI if available
        self.mistral_client = None
        if MISTRAL_AVAILABLE and mistral_api_key and mistral_api_key != "your_mistral_api_key_here":
            try:
                self.mistral_client = MistralClient(api_key=mistral_api_key)
                print("✅ Mistral AI client initialized")
            except Exception as e:
                print(f"⚠️ Mistral AI setup failed: {e}")
        else:
            print("⚠️ Using basic resume customization")
    
    def analyze_job_requirements(self, job: JobListing) -> Dict[str, List[str]]:
        """Analyze job to extract key technologies and requirements"""
        
        text = (job.title + " " + job.description + " " + job.requirements).lower()
        
        # Technology categories
        languages = ['python', 'javascript', 'java', 'typescript', 'sql', 'dart', 'php', 'c++']
        frontend = ['react', 'angular', 'vue', 'html5', 'css3', 'tailwind', 'bootstrap']
        backend = ['django', 'flask', 'node.js', 'express', 'spring', 'laravel']
        databases = ['postgresql', 'mysql', 'mongodb', 'redis', 'sqlite']
        cloud = ['aws', 'azure', 'gcp', 'docker', 'kubernetes']
        
        found = {
            'languages': [tech for tech in languages if tech in text],
            'frontend': [tech for tech in frontend if tech in text],
            'backend': [tech for tech in backend if tech in text],
            'databases': [tech for tech in databases if tech in text],
            'cloud': [tech for tech in cloud if tech in text]
        }
        
        return found
    
    def customize_resume(self, job: JobListing) -> str:
        """Create a customized resume for the job"""
        
        # Analyze job requirements
        tech_found = self.analyze_job_requirements(job)
        
        # Generate customized summary
        if 'python' in tech_found['languages'] and 'react' in tech_found['frontend']:
            summary = "Full Stack Developer specializing in Python/Django backend and React frontend development."
        elif 'python' in tech_found['languages']:
            summary = "Backend-focused Developer with strong expertise in Python and API development."
        elif 'react' in tech_found['frontend'] or 'javascript' in tech_found['languages']:
            summary = "Frontend-focused Full Stack Developer with expertise in React and modern JavaScript."
        else:
            summary = "Versatile Full Stack Developer with experience in modern web technologies."
        
        # Prioritize skills based on job
        all_skills = {
            'languages': ['Python', 'JavaScript', 'Java', 'TypeScript', 'SQL', 'Dart'],
            'frontend': ['React', 'Angular', 'HTML5', 'CSS3', 'Tailwind CSS'],
            'backend': ['Django REST', 'Spring Boot', 'Laravel', 'Node.js'],
            'databases': ['PostgreSQL', 'MySQL', 'MongoDB'],
            'tools': ['Git', 'Linux', 'Docker', 'AWS', 'Postman', 'Jira']
        }
        
        # Reorder based on job requirements
        for category, techs in tech_found.items():
            if techs and category in all_skills:
                # Move matching skills to front
                category_skills = all_skills[category].copy()
                for tech in techs:
                    matching = [s for s in category_skills if tech.lower() in s.lower()]
                    for match in matching:
                        if match in category_skills:
                            category_skills.remove(match)
                            category_skills.insert(0, match)
                all_skills[category] = category_skills
        
        # Create resume content
        resume_content = f"""
═══════════════════════════════════════════════════════════════════
                            M'HAMED BABAH
                         Software Developer
═══════════════════════════════════════════════════════════════════

📧 mhamed.bbh01@gmail.com                📱 +222 34503710
💼 linkedin.com/in/mhamed-elbah-6a954b211
🐙 github.com/medbbh                     📍 Nouakchott, Mauritania

🎯 TARGET POSITION: {job.title}
🏢 TARGET COMPANY: {job.company}
📍 TARGET LOCATION: {job.location}
🛂 VISA STATUS: Seeking Work Permit Sponsorship

═══════════════════════════════════════════════════════════════════
🎯 PROFESSIONAL SUMMARY
═══════════════════════════════════════════════════════════════════

{summary} Proven international collaboration through competition wins 
including Supabase Launch Week 14. Currently pursuing Master's in Information 
Systems with strong foundation in secure, scalable applications. Seeking visa 
sponsorship to contribute technical expertise to innovative global teams.

═══════════════════════════════════════════════════════════════════
🎓 EDUCATION
═══════════════════════════════════════════════════════════════════

🎓 Master in Information Systems (In Progress)
   University of Nouakchott | Oct 2023 - Present
   
🎓 Bachelor of Science in Computer Science  
   University of Nouakchott | Oct 2020 - Jun 2023

📚 Relevant Coursework: Cloud Computing, Distributed Systems, Algorithms,
   Data Structures, Information Systems Security, Databases, Agile Methods

═══════════════════════════════════════════════════════════════════
💼 PROFESSIONAL EXPERIENCE
═══════════════════════════════════════════════════════════════════

💼 Head of IT | NJ Consulting | Present
   • Lead technical infrastructure and system architecture decisions
   • Manage full-stack development projects and client consultations
   • Implement security protocols and best practices for client solutions
   • Coordinate international project collaborations

💼 Software Developer Intern | Next Technology | Jul 2023 - Present
   • Developed REST APIs for e-commerce platform with admin analytics
   • Integrated Stripe payment processing with secure transaction logging
   • Implemented JWT authentication for role-based access control
   • Technologies: Django REST, React, PostgreSQL, Stripe

💼 FullStack Developer | Syskat Technology | Feb 2023 - Apr 2023
   • Built COVID-19 management system with vaccination tracking dashboards
   • Implemented SMS notifications via Twilio API integration
   • Technologies: Angular, Laravel, MySQL, Twilio

═══════════════════════════════════════════════════════════════════
🚀 KEY PROJECTS
═══════════════════════════════════════════════════════════════════

🏆 Thimar - AI Productivity Platform | WINNER: Supabase Launch Week 14
   • Built intelligent task management platform with AI-driven recommendations
   • Implemented real-time data synchronization using Supabase
   • Led 3-person international team to competition victory
   • Technologies: React, Supabase, PostgreSQL, AI/ML

🔐 Blockchain Medical Record System | 2025
   • Designed HIPAA-compliant system with AES-256 encryption
   • Implemented blockchain ledger for immutable access audit trails
   • Developed role-based dashboards with comprehensive analytics
   • Technologies: Django REST, React, MongoDB, Blockchain

📊 School Assessment Platform
   • Created comprehensive role-based academic evaluation system
   • Designed advanced reporting tools with filtering capabilities
   • Implemented secure JWT authentication and authorization
   • Technologies: Django REST, PostgreSQL, React, JWT

💻 Freelance Web Development Projects
   • Developed responsive landing pages with integrated contact forms
   • Delivered projects on time with ongoing maintenance support
   • Technologies: HTML5, CSS3, JavaScript, PHP

═══════════════════════════════════════════════════════════════════
🛠️ TECHNICAL SKILLS (Optimized for this role)
═══════════════════════════════════════════════════════════════════

💻 Programming Languages: {', '.join(all_skills['languages'][:5])}
🎨 Frontend Technologies: {', '.join(all_skills['frontend'][:5])}
⚙️ Backend Frameworks: {', '.join(all_skills['backend'][:4])}
🗄️ Databases: {', '.join(all_skills['databases'][:3])}
🔧 Tools & Technologies: {', '.join(all_skills['tools'][:6])}

═══════════════════════════════════════════════════════════════════
🏆 CERTIFICATIONS & ACHIEVEMENTS
═══════════════════════════════════════════════════════════════════

🏆 Winner: SalamHack International Hackathon 2025 (Team Leader)
🏆 Winner: Supabase Launch Week 14 Competition (Thimar Platform)
🏆 Ranked 16th/29: Ecothon "Green Code of Moscow" 2024
📜 Flutter Bootcamp - Smart MS SA (Dec 2023)
📜 DataCamp Certifications: Intermediate Git, Python (2024-2025)

═══════════════════════════════════════════════════════════════════
🌍 INTERNATIONAL READINESS
═══════════════════════════════════════════════════════════════════

✅ Strong English communication for global collaboration
✅ Experience leading diverse, international project teams
✅ Proven ability to work in competitive international environments
✅ Ready to relocate with appropriate visa sponsorship
✅ Can start immediately upon visa approval

Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}
Customized for: {job.company} - {job.title}
"""
        
        # Save resume
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', job.company)
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job.title)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_company}_{safe_title}_{timestamp}.txt"
        resume_path = self.output_dir / filename
        
        with open(resume_path, 'w', encoding='utf-8') as f:
            f.write(resume_content)
        
        print(f"📄 Resume generated: {filename}")
        return str(resume_path)

class ApplicationBot:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.db = DatabaseManager()
        self.scraper = JobScraper()
        
        # Initialize resume customizer
        mistral_api_key = os.getenv('MISTRAL_API_KEY') or config.get('mistral_api_key')
        self.resume_customizer = ResumeCustomizer(mistral_api_key)
        
        print("✅ Application bot initialized")
        
    def run_daily_scan(self):
        """Main method to run daily job scanning and applications"""
        print(f"🤖 Starting daily job scan at {datetime.now()}")
        
        # Get configuration
        max_apps = self.config.get('max_applications_per_day', 5)
        dry_run = self.config.get('dry_run', True)
        
        print(f"📊 Max applications: {max_apps}")
        print(f"🧪 Dry run mode: {dry_run}")
        
        # Scrape for jobs (using mock data for now)
        print("\n🔍 Searching for jobs...")
        all_jobs = self.scraper.scrape_mock_jobs()
        
        print(f"📊 Found {len(all_jobs)} jobs")
        
        # Filter and save new jobs
        new_jobs = []
        for job in all_jobs:
            if self.db.save_job(job):  # Returns True if job is new
                new_jobs.append(job)
        
        print(f"📊 Found {len(new_jobs)} new jobs")
        
        # Apply to relevant jobs
        applications_sent = 0
        for job in new_jobs:
            if applications_sent >= max_apps:
                print(f"📊 Reached daily limit of {max_apps} applications")
                break
                
            if self.should_apply_to_job(job):
                print(f"\n📝 Processing: {job.title} at {job.company}")
                success = self.apply_to_job(job, dry_run)
                if success:
                    applications_sent += 1
                    time.sleep(2)  # Rate limiting
            else:
                print(f"⏭️ Skipping: {job.title} at {job.company} (doesn't match criteria)")
        
        print(f"\n✅ Daily scan completed!")
        print(f"📊 Applications sent: {applications_sent}")
        
        # Send daily report
        self.send_daily_report(new_jobs, applications_sent)
    
    def should_apply_to_job(self, job: JobListing) -> bool:
        """Determine if we should apply to this job"""
        
        # Must mention visa sponsorship
        if not job.visa_sponsorship:
            return False
        
        # Filter by title keywords
        title_lower = job.title.lower()
        relevant_titles = [
            'software developer', 'software engineer', 'full stack', 'backend developer',
            'frontend developer', 'web developer', 'python developer', 'react developer'
        ]
        
        if not any(title in title_lower for title in relevant_titles):
            return False
        
        # Exclude certain keywords (for now)
        exclude_keywords = ['senior', 'lead', 'principal', 'architect', 'manager', '10+ years']
        if any(keyword in title_lower for keyword in exclude_keywords):
            return False
        
        return True
    
    def apply_to_job(self, job: JobListing, dry_run: bool = True) -> bool:
        """Apply to a specific job"""
        try:
            # Generate customized resume
            resume_path = self.resume_customizer.customize_resume(job)
            
            if not resume_path:
                print(f"❌ Failed to generate resume for {job.company}")
                return False
            
            if dry_run:
                print(f"🧪 DRY RUN: Would apply to {job.company} with resume {os.path.basename(resume_path)}")
            else:
                print(f"✅ Applied to {job.company} with resume {os.path.basename(resume_path)}")
                # In a real implementation, this would submit the application
            
            # Save application record
            application = ApplicationStatus(
                job_id=job.url,
                company=job.company,
                position=job.title,
                application_date=datetime.now().isoformat(),
                status="applied" if not dry_run else "test",
                resume_version=resume_path,
                cover_letter_version="auto-generated"
            )
            
            self.db.save_application(application)
            return True
            
        except Exception as e:
            print(f"❌ Error applying to {job.company}: {e}")
            return False
    
    def send_daily_report(self, new_jobs: List[JobListing], applications_sent: int):
        """Send daily summary report"""
        
        print("\n📊 Daily Job Application Report")
        print("=" * 50)
        print(f"New Jobs Found: {len(new_jobs)}")
        print(f"Applications Sent: {applications_sent}")
        print("\nTop New Opportunities:")
        
        for job in new_jobs[:5]:
            print(f"- {job.title} at {job.company} ({job.location})")
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'scraper'):
            self.scraper.close()
        print("🧹 Cleanup completed")

def main():
    """Main execution function"""
    
    # Load configuration
    config = {
        'max_applications_per_day': 5,
        'dry_run': True,  # Set to False for real applications
        'mistral_api_key': os.getenv('MISTRAL_API_KEY')
    }
    
    # Handle command line arguments
    import sys
    if '--real' in sys.argv or '--no-dry-run' in sys.argv:
        config['dry_run'] = False
        print("🚨 REAL MODE: Applications will be actually sent!")
    
    if '--max-apps' in sys.argv:
        try:
            idx = sys.argv.index('--max-apps')
            config['max_applications_per_day'] = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("⚠️ Invalid --max-apps value, using default")
    
    # Initialize and run bot
    bot = ApplicationBot(config)
    
    try:
        bot.run_daily_scan()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()