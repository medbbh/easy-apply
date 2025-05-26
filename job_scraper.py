import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re
import json
import time
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

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.base_output_dir = Path("job_applications")
        
    def search_and_prepare(self, keywords: List[str], doc_generator, user_profile: Dict = None) -> List[JobResult]:
        self._clear_job_applications_folder()
        
        all_jobs = []
        search_query = ' '.join(keywords)
        
        all_jobs.extend(self._scrape_indeed_comprehensive(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_monster(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_ziprecruiter(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_linkedin_jobs(search_query))
        time.sleep(3)
        all_jobs.extend(self._scrape_careerbuilder(search_query))
        
        unique_jobs = self._remove_duplicates(all_jobs)
        
        results = []
        pdf_count = 0
        
        for job in unique_jobs:
            try:
                folder_name, pdf_generated = self._prepare_application(job, doc_generator, user_profile)
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
        print(f"📄 {pdf_count} PDFs successfully created")
        if user_profile:
            print("👤 Using custom user profile for personalization")
            
        return results
    
    def _clear_job_applications_folder(self):
        if self.base_output_dir.exists():
            shutil.rmtree(self.base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
    
    def _prepare_application(self, job: Dict, doc_generator, user_profile: Dict = None) -> tuple[str, bool]:
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', job['company'])
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job['title'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        folder_name = f"{safe_company}_{safe_title}_{timestamp}"
        job_folder = self.base_output_dir / folder_name
        job_folder.mkdir(exist_ok=True)
        
        with open(job_folder / "job_info.json", 'w', encoding='utf-8') as f:
            json.dump(job, f, indent=2, ensure_ascii=False)
        
        # Pass user_profile to document generator
        resume_pdf = doc_generator.generate_resume(job, job_folder, user_profile)
        cover_letter_pdf = doc_generator.generate_cover_letter(job, job_folder, user_profile)
        
        pdf_generated = bool(resume_pdf or cover_letter_pdf)
        
        return folder_name, pdf_generated
    
    def _scrape_indeed_comprehensive(self, search_query: str) -> List[Dict]:
        jobs = []
        
        try:
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
                    
                    job_containers = (
                        soup.find_all('div', class_='job_seen_beacon') or
                        soup.find_all('div', class_='slider_container') or
                        soup.find_all('div', class_='jobsearch-SerpJobCard') or
                        soup.find_all('a', {'data-jk': True}) or
                        soup.find_all('div', {'data-jk': True})
                    )
                    
                    for container in job_containers[:12]:
                        try:
                            job = self._extract_indeed_job(container)
                            if job:
                                jobs.append(job)
                        except:
                            continue
                            
                    time.sleep(2)
                    
                except:
                    continue
                    
        except:
            pass
        
        return jobs
    
    def _extract_indeed_job(self, container) -> Optional[Dict]:
        try:
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
            
            company_elem = (
                container.find('span', class_='companyName') or
                container.find('a', {'data-testid': 'company-name'}) or
                container.find('div', class_='companyName') or
                container.find('span', class_='company')
            )
            
            if not company_elem:
                return None
                
            company = company_elem.get_text(strip=True)
            
            location_elem = (
                container.find('div', class_='companyLocation') or
                container.find('div', {'data-testid': 'job-location'}) or
                container.find('span', class_='location')
            )
            
            location = location_elem.get_text(strip=True) if location_elem else "Various Locations"
            
            link_elem = container.find('a', {'data-jk': True}) or title_elem
            if link_elem and link_elem.get('href'):
                job_url = urljoin("https://www.indeed.com", link_elem['href'])
            elif link_elem and link_elem.get('data-jk'):
                job_url = f"https://www.indeed.com/viewjob?jk={link_elem['data-jk']}"
            else:
                job_url = f"https://www.indeed.com/jobs?q={quote_plus(title)}"
            
            salary_elem = (
                container.find('span', class_='salary-snippet') or
                container.find('div', class_='salary-snippet-container') or
                container.find('span', class_='estimated-salary')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else "Competitive"
            
            snippet_elem = (
                container.find('div', class_='job-snippet') or
                container.find('span', class_='summary') or
                container.find('div', class_='summary')
            )
            description = snippet_elem.get_text(strip=True) if snippet_elem else f"{title} position at {company} in {location}."
            
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
        jobs = []
        
        try:
            url = f"https://www.monster.com/jobs/search?q={quote_plus(search_query)}&where=__2C-US&page=1"
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
        jobs = []
        
        try:
            url = f"https://www.ziprecruiter.com/jobs-search?search={quote_plus(search_query)}&location="
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
                    
                    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                    job_url = urljoin("https://www.ziprecruiter.com", link_elem['href']) if link_elem and link_elem.get('href') else f"https://www.ziprecruiter.com/jobs-search?search={quote_plus(search_query)}"
                    
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
        jobs = []
        
        try:
            encoded_query = quote_plus(search_query)
            
            search_urls = [
                f"https://www.linkedin.com/jobs/search?keywords={encoded_query}&location=&geoId=&f_TPR=r604800",
                f"https://www.linkedin.com/jobs/search?keywords={encoded_query}&location=United%20States&f_TPR=r604800",
            ]
            
            for search_url in search_urls[:2]:
                try:
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
                    
                    job_containers = (
                        soup.find_all('div', class_='base-card') or
                        soup.find_all('div', class_='base-search-card') or
                        soup.find_all('li', class_='result-card') or
                        soup.find_all('div', {'data-entity-urn': True}) or
                        soup.find_all('article', class_='job-card')
                    )
                    
                    for container in job_containers[:8]:
                        try:
                            job = self._extract_linkedin_job(container, encoded_query)
                            if job:
                                jobs.append(job)
                        except:
                            continue
                    
                    time.sleep(3)
                    
                except:
                    continue
                    
        except:
            pass
        
        if len(jobs) == 0:
            jobs.extend(self._create_linkedin_fallback_jobs(search_query))
        
        return jobs
    
    def _extract_linkedin_job(self, container, encoded_query: str) -> Optional[Dict]:
        try:
            title_elem = (
                container.find('h3', class_='base-search-card__title') or
                container.find('a', class_='result-card__title-link') or
                container.find('h3') or
                container.find('a', {'data-tracking-will-navigate': True})
            )
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 3:
                return None
            
            company_elem = (
                container.find('h4', class_='base-search-card__subtitle') or
                container.find('a', class_='result-card__subtitle-link') or
                container.find('h4')
            )
            
            company = company_elem.get_text(strip=True) if company_elem else "LinkedIn Company"
            
            location_elem = (
                container.find('span', class_='job-result-card__location') or
                container.find('span', class_='result-card__location') or
                container.find('div', class_='base-search-card__metadata')
            )
            
            location = location_elem.get_text(strip=True) if location_elem else "Various Locations"
            
            job_url = self._construct_linkedin_job_url(container, title, company, encoded_query)
            
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
        job_id = None
        
        for attr in ['data-entity-urn', 'data-job-id', 'data-tracking-will-navigate']:
            if container.get(attr):
                attr_value = container[attr]
                job_id_match = re.search(r'(\d{10,})', attr_value)
                if job_id_match:
                    job_id = job_id_match.group(1)
                    break
        
        if not job_id:
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                job_id_match = re.search(r'/jobs/view/(\d+)', href)
                if job_id_match:
                    job_id = job_id_match.group(1)
        
        if job_id:
            return f"https://www.linkedin.com/jobs/view/{job_id}"
        
        search_terms = f"{title} {company}".replace(' ', '%20')
        return f"https://www.linkedin.com/jobs/search?keywords={search_terms}&location=&geoId="
    
    def _create_linkedin_fallback_jobs(self, search_query: str) -> List[Dict]:
        job_variations = []
        query_lower = search_query.lower()
        
        if 'analyst' in query_lower:
            job_variations = [
                ("Data Analyst", "Tech Company"),
                ("Business Analyst", "Consulting Firm"), 
                ("Research Analyst", "Financial Services")
            ]
        elif 'developer' in query_lower or 'engineer' in query_lower:
            job_variations = [
                ("Software Developer", "Technology Company"),
                ("Frontend Developer", "Startup"),
                ("Backend Engineer", "Software Company")
            ]
        elif 'marketing' in query_lower:
            job_variations = [
                ("Marketing Coordinator", "Marketing Agency"),
                ("Digital Marketing Specialist", "E-commerce Company")
            ]
        else:
            job_variations = [
                (f"{search_query.title()} Specialist", "Professional Services"),
                (f"{search_query.title()} Associate", "Industry Leader")
            ]
        
        fallback_jobs = []
        
        for job_title, company_type in job_variations[:3]:
            search_url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(job_title)}&location=&geoId="
            
            fallback_jobs.append({
                'title': job_title,
                'company': f"{company_type} (LinkedIn Search)",
                'location': "Multiple Locations",
                'description': f"Browse {job_title} opportunities on LinkedIn. This search will show you current openings that match your criteria.",
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
        jobs = []
        
        try:
            url = f"https://www.careerbuilder.com/jobs?keywords={quote_plus(search_query)}&location="
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
                    
                    location = "Various Locations"
                    
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
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job['title'].lower()}_{job['company'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _check_visa_friendly(self, text: str) -> bool:
        visa_indicators = [
            'visa sponsorship', 'h1b', 'work permit', 'immigration support',
            'international candidates', 'work authorization', 'sponsor visa',
            'remote', 'global', 'worldwide', 'international'
        ]
        return any(indicator in text.lower() for indicator in visa_indicators)
    
    def _extract_skills_from_text(self, text: str) -> str:
        all_skills = [
            'python', 'javascript', 'java', 'react', 'django', 'node.js', 'sql', 'html', 'css',
            'git', 'docker', 'aws', 'azure', 'kubernetes', 'typescript', 'angular', 'vue',
            'communication', 'leadership', 'management', 'analysis', 'excel', 'powerpoint',
            'marketing', 'sales', 'customer service', 'design', 'photoshop', 'illustrator'
        ]
        
        found_skills = [skill.title() for skill in all_skills if skill in text.lower()]
        return ', '.join(found_skills[:6]) if found_skills else "Various professional skills"
    
    def _extract_tech_from_text(self, text: str) -> str:
        tech_skills = [
            'python', 'javascript', 'java', 'react', 'django', 'node.js', 'sql', 'html', 'css',
            'git', 'docker', 'aws', 'azure', 'typescript', 'angular', 'vue', 'php', 'c++', 'c#'
        ]
        
        found_tech = [tech.title() for tech in tech_skills if tech in text.lower()]
        return ', '.join(found_tech[:4]) if found_tech else "Professional tools"
    
    def _get_experience_level(self, title: str) -> str:
        title_lower = title.lower()
        if any(word in title_lower for word in ['senior', 'sr', 'lead', 'principal', 'manager', 'director']):
            return 'Senior'
        elif any(word in title_lower for word in ['junior', 'jr', 'entry', 'graduate', 'intern', 'associate']):
            return 'Junior'
        else:
            return 'Mid-level'