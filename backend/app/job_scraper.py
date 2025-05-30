import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import time
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse, urlencode
from dataclasses import dataclass, asdict
from functools import lru_cache
import random
import logging
import html
from email.utils import parsedate_to_datetime
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function for flexible date parsing
def parse_date_flexible(date_str: Optional[str]) -> str:
    """Tries to parse a date string from common formats."""
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
    
    # Handle relative dates
    date_str_lower = date_str.lower()
    if 'today' in date_str_lower or 'just now' in date_str_lower:
        return datetime.now().strftime('%Y-%m-%d')
    elif 'yesterday' in date_str_lower:
        return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'days ago' in date_str_lower:
        match = re.search(r'(\d+)\s*days?\s*ago', date_str_lower)
        if match:
            days = int(match.group(1))
            return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    elif 'weeks ago' in date_str_lower:
        match = re.search(r'(\d+)\s*weeks?\s*ago', date_str_lower)
        if match:
            weeks = int(match.group(1))
            return (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    elif 'months ago' in date_str_lower:
        match = re.search(r'(\d+)\s*months?\s*ago', date_str_lower)
        if match:
            months = int(match.group(1))
            return (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
    
    # Attempt 1: ISO 8601 (e.g., "2023-10-26T15:00:00Z" or "2023-10-26 15:00:00")
    try:
        temp_date_str = date_str
        if temp_date_str.endswith('Z'):
            temp_date_str = temp_date_str[:-1] + '+00:00'
        # Replace space with T if it's likely ISO format without T
        if ' ' in temp_date_str and 'T' not in temp_date_str and temp_date_str.count(':') >= 2:
             parts = temp_date_str.split(' ')
             if len(parts) == 2 and '-' in parts[0] and ':' in parts[1]:
                temp_date_str = 'T'.join(parts)
        
        dt_obj = datetime.fromisoformat(temp_date_str)
        return dt_obj.strftime('%Y-%m-%d')
    except ValueError:
        pass

    # Attempt 2: RFC 822 (common in RSS, e.g., "Wed, 02 Oct 2002 08:00:00 EST")
    try:
        dt_obj = parsedate_to_datetime(date_str)
        return dt_obj.strftime('%Y-%m-%d')
    except (TypeError, ValueError):
        pass
        
    # Attempt 3: Other common formats (add as needed)
    common_manual_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%b %d, %Y', # Jan 01, 2023
        '%d %b %Y',   # 01 Jan 2023
        '%m/%d/%Y',   # 01/01/2023
        '%B %d, %Y', # January 01, 2023
        '%d/%m/%Y',   # 01/01/2023 (European format)
    ]
    for fmt in common_manual_formats:
        try:
            dt_obj = datetime.strptime(date_str, fmt)
            return dt_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
            
    logger.warning(f"Could not parse date: '{date_str}'. Using current date.")
    return datetime.now().strftime('%Y-%m-%d')

@dataclass
class JobPosting:
    """Enhanced job posting data structure."""
    id: str
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    technologies: List[str]
    salary_range: Optional[str]
    experience_level: str  # junior, mid, senior
    remote_friendly: bool
    visa_sponsorship: bool
    posted_date: str
    source: str
    url: str
    relevance_score: float  # 0-100 match to search
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    benefits: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        return asdict(self)

class JobScraper:
    """Improved job scraper with multiple sources and fallbacks."""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        self.session.headers.update({'User-Agent': random.choice(self.user_agents)})
        
        # Technology synonyms for better matching
        self.tech_synonyms = {
            'javascript': ['js', 'javascript', 'node', 'nodejs', 'ecmascript'],
            'python': ['python', 'py', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'react': ['react', 'reactjs', 'react.js', 'redux'],
            'angular': ['angular', 'angularjs', 'angular.js'],
            'vue': ['vue', 'vuejs', 'vue.js', 'nuxt'],
            'java': ['java', 'spring', 'springboot', 'hibernate', 'jvm'],
            'golang': ['go', 'golang'],
            'csharp': ['c#', 'csharp', '.net', 'dotnet', 'asp.net'],
            'php': ['php', 'laravel', 'symfony', 'wordpress'],
            'ruby': ['ruby', 'rails', 'rubyonrails', 'ror'],
            'swift': ['swift', 'ios', 'swiftui'],
            'kotlin': ['kotlin', 'android'],
            'typescript': ['typescript', 'ts'],
            'rust': ['rust', 'rustlang'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'devops'],
            'container': ['docker', 'kubernetes', 'k8s', 'containerization']
        }

    def get_random_user_agent(self) -> str:
        """Get a random user agent to avoid blocking."""
        return random.choice(self.user_agents)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Unescape HTML entities first
        text = html.unescape(text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-\.,!?()]+', '', text)
        # Trim and limit length
        text = text.strip()
        if len(text) > 1000:
            text = text[:997] + '...'
        return text

    def extract_salary_range(self, text: str) -> Optional[str]:
        """Extract salary range from job text."""
        # Look for salary patterns
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',  # $100,000 - $150,000
            r'\$[\d,]+k?\s*-\s*\$[\d,]+k?',  # $100k - $150k
            r'[\d,]+\s*-\s*[\d,]+\s*(?:USD|EUR|GBP)',  # 100,000 - 150,000 USD
            r'€[\d,]+\s*-\s*€[\d,]+',  # €100,000 - €150,000
            r'£[\d,]+\s*-\s*£[\d,]+',  # £100,000 - £150,000
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None

    def extract_technologies(self, text: str) -> List[str]:
        """Extract technologies from job text."""
        text_lower = text.lower()
        found_techs = set()
        
        # Extended list of technologies to look for
        technologies = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node.js', 'nodejs',
            'django', 'flask', 'fastapi', 'spring', 'typescript', 'php', 'ruby', 'rails',
            'go', 'golang', 'rust', 'c++', 'c#', '.net', 'sql', 'postgresql', 'mysql',
            'mongodb', 'redis', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform',
            'git', 'linux', 'html', 'css', 'sass', 'webpack', 'jenkins', 'graphql',
            'elasticsearch', 'kafka', 'rabbitmq', 'nginx', 'apache', 'pandas', 'numpy',
            'tensorflow', 'pytorch', 'scikit-learn', 'spark', 'hadoop', 'scala', 'kotlin',
            'swift', 'objective-c', 'flutter', 'xamarin', 'unity', 'unreal', 'matlab',
            'r', 'sas', 'tableau', 'power bi', 'excel', 'jira', 'confluence', 'slack'
        ]
        
        for tech in technologies:
            if tech.lower() in text_lower:
                found_techs.add(tech.title())
        
        return list(found_techs)[:15]  # Limit to 15 technologies

    def extract_benefits(self, text: str) -> List[str]:
        """Extract benefits from job description."""
        text_lower = text.lower()
        benefits = []
        
        benefit_keywords = {
            'health insurance': ['health insurance', 'medical insurance', 'healthcare', 'medical coverage'],
            'dental insurance': ['dental insurance', 'dental coverage', 'dental plan'],
            'vision insurance': ['vision insurance', 'vision coverage', 'vision plan'],
            '401k': ['401k', '401(k)', 'retirement plan', 'pension'],
            'paid time off': ['pto', 'paid time off', 'vacation days', 'holiday pay'],
            'remote work': ['remote work', 'work from home', 'wfh', 'telecommute'],
            'flexible hours': ['flexible hours', 'flex time', 'flexible schedule'],
            'stock options': ['stock options', 'equity', 'espp', 'rsu'],
            'bonus': ['bonus', 'performance bonus', 'annual bonus'],
            'parental leave': ['parental leave', 'maternity leave', 'paternity leave'],
            'professional development': ['professional development', 'training budget', 'conference budget'],
            'gym membership': ['gym membership', 'fitness benefit', 'wellness program']
        }
        
        for benefit, keywords in benefit_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                benefits.append(benefit)
        
        return benefits[:8]  # Limit to 8 benefits

    def detect_job_type(self, text: str) -> str:
        """Detect job type from text."""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['full-time', 'full time', 'ft']):
            return 'Full-time'
        elif any(term in text_lower for term in ['part-time', 'part time', 'pt']):
            return 'Part-time'
        elif any(term in text_lower for term in ['contract', 'contractor', 'freelance']):
            return 'Contract'
        elif any(term in text_lower for term in ['internship', 'intern']):
            return 'Internship'
        elif any(term in text_lower for term in ['temporary', 'temp']):
            return 'Temporary'
        else:
            return 'Full-time'  # Default

    def detect_experience_level(self, title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        # Frontend options for reference: const experienceLevels = ["Entry-level", "Junior", "Mid-level", "Senior", "Lead", "Principal"];
        # Order matters: check from most senior/specific to most junior/general.

        # Principal
        principal_kws = ['principal engineer', 'principal software engineer', 'principal architect', 'principal consultant']
        if any(kw in text for kw in principal_kws):
            return "Principal"

        # Lead
        lead_kws = ['lead engineer', 'tech lead', 'team lead', 'lead developer', 'development lead', 'engineering lead']
        if any(kw in text for kw in lead_kws):
            return "Lead"
        
        # Senior
        senior_kws = ['senior', 'sr.', 'sr ', 'staff engineer', 'architect', # Architect often implies senior
                      'manager', 'director', 'expert', 'head of', 
                      '7+ years', '8+ years', '9+ years', '10+ years', '10+ yrs', '7+ yrs', 'seven years', 'eight years', 'ten years']
        if any(kw in text for kw in senior_kws):
            return "Senior"

        # Mid-level
        # Note: 'software engineer' without other qualifiers often implies mid-level. This is hard with keywords alone.
        mid_kws = ['mid-level', 'mid level', 'intermediate', 'mid-senior', 
                   '3-5 years', '4-6 years', '5-7 years', '3+ years', '3+ yrs', 'three years', 'four years', 'five years',
                   'engineer ii', 'developer ii']
        if any(kw in text for kw in mid_kws):
            return "Mid-level"

        # Junior - check before entry if specific junior terms are present and not entry terms
        junior_kws = ['junior', 'jr.', 'jr ', 'associate software engineer', 'associate developer', 
                      '1-3 years', '1-2 yrs', '2-3 years', 'one year', 'two years', 'three years experience', # "three years" could be mid, context matters
                      'engineer i', 'developer i']
        
        # Entry-level - has more specific terms like intern, graduate
        entry_kws = ['entry-level', 'entry level', 'graduate', 'new grad', 'graduating',
                     'intern', 'internship', 'trainee', 
                     '0-1 year', '0-2 years', '<1 year', '<2 years', 'no experience required', 'recent graduate']

        has_junior_term = any(kw in text for kw in junior_kws)
        has_entry_term = any(kw in text for kw in entry_kws)

        if has_entry_term: # Prioritize "Entry-level" if its specific keywords are found
            return "Entry-level"
        if has_junior_term: # If no entry-specific terms, but junior terms, then "Junior"
            return "Junior"
        
        # Fallback title checks (less reliable than full text but good for some cases)
        # These are checked if the above keyword checks on full text didn't return.
        title_lower = title.lower()
        if 'principal' in title_lower: return "Principal"
        if 'lead' in title_lower: return "Lead"
        if 'senior' in title_lower or 'sr ' in title_lower: return "Senior"
        # Check for mid-level in title if possible, though less common as explicit term
        if 'mid-level' in title_lower or 'mid level' in title_lower: return "Mid-level"
        if 'junior' in title_lower or 'jr ' in title_lower: return "Junior"
        if 'entry' in title_lower or 'intern' in title_lower or 'graduate' in title_lower : return "Entry-level"
        
        # Default if nothing clearly matches after all checks
        return "Mid-level"

    def detect_remote_friendly(self, location: str, description: str) -> bool:
        """Detect if job is remote-friendly."""
        text = f"{location} {description}".lower()
        remote_indicators = ['remote', 'work from home', 'distributed', 'anywhere', 
                           'telecommute', 'wfh', 'virtual', 'home office', 'remote-first']
        return any(indicator in text for indicator in remote_indicators)

    def detect_visa_sponsorship(self, description: str) -> bool:
        """Detect if job offers visa sponsorship."""
        text = description.lower()
        visa_indicators = [
            'visa sponsorship', 'h1b', 'h-1b', 'work permit', 'immigration support',
            'international candidates', 'work authorization', 'sponsor visa',
            'visa assistance', 'green card', 'employment authorization'
        ]
        
        # Also check for negative indicators
        no_visa_indicators = [
            'no visa sponsorship', 'cannot sponsor', 'unable to sponsor',
            'must be authorized', 'must have work authorization',
            'citizen or permanent resident'
        ]
        
        if any(indicator in text for indicator in no_visa_indicators):
            return False
        
        return any(indicator in text for indicator in visa_indicators)

    def calculate_relevance_score(self, job_text: str, keywords: str) -> float:
        """Calculate relevance score between job and search keywords."""
        job_text_lower = job_text.lower()
        keywords_lower = keywords.lower()
        
        # Define conflicting terms - if user searches for one, exclude the others
        experience_conflicts = {
            'junior': ['senior', 'lead', 'principal', 'staff', 'architect', 'manager', 'director', 'head of'],
            'entry': ['senior', 'lead', 'principal', 'staff', 'architect', 'manager', 'director', 'head of', 'mid-level', 'experienced'],
            'entry-level': ['senior', 'lead', 'principal', 'staff', 'architect', 'manager', 'director', 'head of', 'mid-level', 'experienced'],
            'intern': ['senior', 'lead', 'principal', 'staff', 'architect', 'manager', 'director', 'head of', 'mid-level', 'experienced'],
            'senior': ['junior', 'entry', 'entry-level', 'intern', 'trainee', 'graduate'],
            'lead': ['junior', 'entry', 'entry-level', 'intern', 'trainee', 'graduate'],
            'principal': ['junior', 'entry', 'entry-level', 'intern', 'trainee', 'graduate', 'mid-level'],
        }
        
        # Add job type conflicts
        job_type_conflicts = {
            'full-time': ['part-time', 'contract', 'freelance', 'temporary', 'intern'],
            'part-time': ['full-time'],
            'contract': ['full-time', 'permanent'],
            'freelance': ['full-time', 'permanent'],
            'permanent': ['contract', 'freelance', 'temporary'],
            'remote': ['on-site only', 'in-office only'],
        }
        
        # Check for conflicting terms
        for search_term, conflicts in experience_conflicts.items():
            if search_term in keywords_lower:
                # If any conflicting term is found in the job text, return 0 score
                for conflict in conflicts:
                    if conflict in job_text_lower:
                        return 0.0
        
        # Check job type conflicts
        for search_term, conflicts in job_type_conflicts.items():
            if search_term in keywords_lower:
                for conflict in conflicts:
                    if conflict in job_text_lower:
                        return 0.0
        
        # Split keywords by common delimiters
        keyword_list = re.split(r'[,\s]+', keywords_lower)
        keyword_list = [k.strip() for k in keyword_list if k.strip()]
        
        score = 0.0
        total_keywords = len(keyword_list)
        
        for keyword in keyword_list:
            if not keyword:
                continue
                
            # Direct match
            if keyword in job_text_lower:
                score += 20.0
            
            # Check synonyms
            for tech, synonyms in self.tech_synonyms.items():
                if keyword in synonyms and any(syn in job_text_lower for syn in synonyms):
                    score += 15.0
                    break
            
            # Partial match (only for longer keywords to avoid false positives)
            if len(keyword) > 3:
                keyword_parts = keyword.split()
                if any(part in job_text_lower for part in keyword_parts if len(part) > 3):
                    score += 5.0
        
        # Normalize score
        max_possible_score = total_keywords * 20.0
        if max_possible_score > 0:
            score = min(100.0, (score / max_possible_score) * 100)
        
        return round(score, 1)

    @lru_cache(maxsize=100)
    def scrape_remoteok(self, keywords: str, max_jobs: int = 10) -> List[JobPosting]:
        """Scrape RemoteOK API - most reliable source."""
        jobs = []
        try:
            logger.info("Scraping RemoteOK...")
            url = "https://remoteok.com/api"
            headers = {'User-Agent': self.get_random_user_agent()}
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Skip first item (metadata)
            job_data = data[1:] if isinstance(data, list) and len(data) > 1 else data
            
            for job in job_data:
                if not isinstance(job, dict) or len(jobs) >= max_jobs:
                    continue
                
                title = job.get('position', '').strip()
                company = job.get('company', '').strip()
                description = job.get('description', '').strip()
                
                if not title or not company:
                    continue
                
                # Calculate relevance
                job_text = f"{title} {company} {description}"
                relevance = self.calculate_relevance_score(job_text, keywords)
                
                # Only include relevant jobs
                if relevance < 20:
                    continue
                
                # Extract salary
                salary_min = job.get('salary_min')
                salary_max = job.get('salary_max')
                salary_range = None
                if salary_min and salary_max:
                    salary_range = f"${salary_min:,} - ${salary_max:,}"
                
                job_posting = JobPosting(
                    id=f"remoteok_{job.get('id', len(jobs))}",
                    title=title,
                    company=company,
                    location='Remote',
                    description=self.clean_text(description),
                    requirements=job.get('tags', [])[:5] if job.get('tags') else [],
                    technologies=self.extract_technologies(job_text),
                    salary_range=salary_range,
                    experience_level=self.detect_experience_level(title, description),
                    remote_friendly=True,
                    visa_sponsorship=self.detect_visa_sponsorship(description),
                    posted_date=parse_date_flexible(job.get('date')),
                    source='RemoteOK',
                    url=job.get('url', ''),
                    relevance_score=relevance,
                    job_type='Full-time',
                    benefits=['Remote work', 'Flexible hours']
                )
                jobs.append(job_posting)
                
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {e}")
        
        return jobs

    def scrape_linkedin(self, keywords: str, location: str = "", max_jobs: int = 10) -> List[JobPosting]:
        """Scrape LinkedIn jobs (limited without login)."""
        jobs = []
        try:
            logger.info("Scraping LinkedIn jobs...")
            
            # LinkedIn public job search URL
            params = {
                'keywords': keywords,
                'location': location or 'United States',
                'f_TPR': 'r86400',  # Past 24 hours
                'position': 1,
                'pageNum': 0
            }
            
            base_url = 'https://www.linkedin.com/jobs/search'
            url = f"{base_url}?{urlencode(params)}"
            
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')[:max_jobs]
            
            for i, card in enumerate(job_cards):
                try:
                    # Extract job details
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    location_elem = card.find('span', class_='job-search-card__location')
                    link_elem = card.find('a', class_='base-card__full-link')
                    
                    if not all([title_elem, company_elem, link_elem]):
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    job_location = location_elem.text.strip() if location_elem else location
                    job_url = link_elem.get('href', '')
                    
                    # Extract time posted
                    time_elem = card.find('time')
                    posted_date = parse_date_flexible(time_elem.get('datetime', '') if time_elem else '')
                    
                    # Create job description from available info
                    description = f"{title} position at {company} in {job_location}. "
                    
                    # Extract any additional metadata
                    metadata_elem = card.find('div', class_='base-search-card__metadata')
                    if metadata_elem:
                        description += metadata_elem.text.strip()
                    
                    job_text = f"{title} {company} {description}"
                    relevance = self.calculate_relevance_score(job_text, keywords)
                    
                    if relevance < 15:
                        continue
                    
                    job_posting = JobPosting(
                        id=f"linkedin_{hashlib.md5(job_url.encode()).hexdigest()[:8]}",
                        title=title,
                        company=company,
                        location=job_location,
                        description=self.clean_text(description),
                        requirements=self.extract_technologies(job_text)[:5],
                        technologies=self.extract_technologies(job_text),
                        salary_range=self.extract_salary_range(description),
                        experience_level=self.detect_experience_level(title, description),
                        remote_friendly=self.detect_remote_friendly(job_location, description),
                        visa_sponsorship=self.detect_visa_sponsorship(description),
                        posted_date=posted_date,
                        source='LinkedIn',
                        url=job_url,
                        relevance_score=relevance,
                        job_type=self.detect_job_type(description),
                        benefits=self.extract_benefits(description)
                    )
                    jobs.append(job_posting)
                    
                except Exception as e:
                    logger.debug(f"Error parsing LinkedIn job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        
        return jobs

    def scrape_indeed(self, keywords: str, location: str = "", max_jobs: int = 10) -> List[JobPosting]:
        """Scrape Indeed jobs."""
        jobs = []
        try:
            logger.info("Scraping Indeed jobs...")
            
            # Indeed search URL
            params = {
                'q': keywords,
                'l': location or 'United States',
                'fromage': '7',  # Jobs from last 7 days
                'sort': 'date'
            }
            
            url = f"https://www.indeed.com/jobs?{urlencode(params)}"
            
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Indeed uses different class names periodically, try multiple selectors
            job_cards = soup.find_all('div', class_='job_seen_beacon') or \
                       soup.find_all('div', class_='jobsearch-SerpJobCard') or \
                       soup.find_all('div', class_='slider_container')
            
            job_cards = job_cards[:max_jobs]
            
            for i, card in enumerate(job_cards):
                try:
                    # Extract job details with multiple selector attempts
                    title_elem = card.find('h2', class_='jobTitle') or \
                                card.find('a', {'data-testid': 'job-title'}) or \
                                card.find('span', {'title': True})
                    
                    company_elem = card.find('div', {'data-testid': 'company-name'}) or \
                                  card.find('span', class_='companyName') or \
                                  card.find('a', {'data-testid': 'company-name'})
                    
                    location_elem = card.find('div', {'data-testid': 'job-location'}) or \
                                   card.find('div', class_='locationsContainer') or \
                                   card.find('span', class_='location')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else 'Company'
                    job_location = location_elem.text.strip() if location_elem else location
                    
                    # Build job URL
                    link_elem = card.find('a', href=True)
                    if link_elem and link_elem.get('href'):
                        job_url = f"https://www.glassdoor.com{link_elem['href']}" if link_elem['href'].startswith('/') else link_elem['href']
                    else:
                        job_url = url
                    
                    # Create description
                    description = f"{title} position at {company} in {job_location}."
                    
                    # Extract salary if available
                    salary_elem = card.find('span', class_='salary-estimate') or \
                                 card.find('span', {'data-test': 'detailSalary'})
                    salary = salary_elem.text.strip() if salary_elem else None
                    
                    job_text = f"{title} {company} {description}"
                    relevance = self.calculate_relevance_score(job_text, keywords)
                    
                    if relevance < 15:
                        continue
                    
                    job_posting = JobPosting(
                        id=f"glassdoor_{hashlib.md5(job_url.encode()).hexdigest()[:8]}",
                        title=title,
                        company=company,
                        location=job_location,
                        description=self.clean_text(description),
                        requirements=self.extract_technologies(job_text)[:5],
                        technologies=self.extract_technologies(job_text),
                        salary_range=salary or self.extract_salary_range(description),
                        experience_level=self.detect_experience_level(title, description),
                        remote_friendly=self.detect_remote_friendly(job_location, description),
                        visa_sponsorship=self.detect_visa_sponsorship(description),
                        posted_date=datetime.now().strftime('%Y-%m-%d'),
                        source='Glassdoor',
                        url=job_url,
                        relevance_score=relevance,
                        job_type=self.detect_job_type(description),
                        benefits=[]
                    )
                    jobs.append(job_posting) if hasattr(title_elem, 'text') else title_elem.get('title', '')
                    company = company_elem.text.strip() if company_elem else 'Company'
                    job_location = location_elem.text.strip() if location_elem else location
                    
                    # Extract job URL
                    link_elem = card.find('a', {'class': 'jcs-JobTitle'}) or \
                               card.find('a', {'data-testid': 'job-title'}) or \
                               card.find('a', href=True)
                    
                    if link_elem and link_elem.get('href'):
                        job_url = f"https://www.indeed.com{link_elem['href']}" if link_elem['href'].startswith('/') else link_elem['href']
                    else:
                        job_url = url
                    
                    # Extract snippet/description
                    snippet_elem = card.find('div', class_='job-snippet') or \
                                  card.find('div', {'class': 'summary'}) or \
                                  card.find('div', {'data-testid': 'job-snippet'})
                    
                    description = snippet_elem.text.strip() if snippet_elem else f"{title} at {company}"
                    
                    # Extract salary if available
                    salary_elem = card.find('div', class_='salary-snippet') or \
                                 card.find('span', class_='salary')
                    salary = salary_elem.text.strip() if salary_elem else None
                    
                    # Extract posted date
                    date_elem = card.find('span', class_='date') or \
                               card.find('span', {'data-testid': 'job-posted-date'})
                    posted_date = parse_date_flexible(date_elem.text.strip() if date_elem else '')
                    
                    job_text = f"{title} {company} {description}"
                    relevance = self.calculate_relevance_score(job_text, keywords)
                    
                    if relevance < 15:
                        continue
                    
                    job_posting = JobPosting(
                        id=f"indeed_{hashlib.md5(job_url.encode()).hexdigest()[:8]}",
                        title=title,
                        company=company,
                        location=job_location,
                        description=self.clean_text(description),
                        requirements=self.extract_technologies(job_text)[:5],
                        technologies=self.extract_technologies(job_text),
                        salary_range=salary or self.extract_salary_range(description),
                        experience_level=self.detect_experience_level(title, description),
                        remote_friendly=self.detect_remote_friendly(job_location, description),
                        visa_sponsorship=self.detect_visa_sponsorship(description),
                        posted_date=posted_date,
                        source='Indeed',
                        url=job_url,
                        relevance_score=relevance,
                        job_type=self.detect_job_type(description),
                        benefits=self.extract_benefits(description)
                    )
                    jobs.append(job_posting)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Indeed job card: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
        
        return jobs

    def scrape_all_sources(self, keywords: str, location: str = "", max_total: int = 25) -> List[JobPosting]:
        """Scrape from specified real sources only."""
        all_jobs = []
        
        try:
            logger.info(f"Starting REAL job search for: {keywords}, Location: {location if location else 'Any'}")
            
            # LinkedIn (target: ~10 jobs)
            linkedin_jobs = self.scrape_linkedin(keywords, location, max_jobs=10)
            all_jobs.extend(linkedin_jobs)
            logger.info(f"Scraped {len(linkedin_jobs)} jobs from LinkedIn.")
            time.sleep(random.uniform(1.0, 2.5)) # Be respectful
            
            # Indeed (target: ~10 jobs)
            indeed_jobs = self.scrape_indeed(keywords, location, max_jobs=10)
            all_jobs.extend(indeed_jobs)
            logger.info(f"Scraped {len(indeed_jobs)} jobs from Indeed.")
            time.sleep(random.uniform(1.0, 2.5))
            
            # RemoteOK (API - target: ~5 jobs)
            remoteok_jobs = self.scrape_remoteok(keywords, max_jobs=5)
            all_jobs.extend(remoteok_jobs)
            logger.info(f"Scraped {len(remoteok_jobs)} jobs from RemoteOK.")
            
            logger.info(f"Scraped a total of {len(all_jobs)} potential jobs from all real sources.")
            
        except Exception as e:
            logger.error(f"Error in main scraping loop: {e}")
        
        # Deduplicate jobs
        unique_jobs_dict = {}
        for job in all_jobs:
            # Use a tuple of critical fields for deduplication key
            key = (job.title.lower().strip(), 
                   job.company.lower().strip(), 
                   job.location.lower().strip(), 
                   job.source.lower().strip() # Add source to key for more precise deduplication
                  )
            
            # Prioritize jobs with higher relevance or more complete URLs if duplicate
            if key not in unique_jobs_dict or \
               job.relevance_score > unique_jobs_dict[key].relevance_score or \
               (job.relevance_score == unique_jobs_dict[key].relevance_score and len(job.url) > len(unique_jobs_dict[key].url) and job.url != unique_jobs_dict[key].url) or \
               (job.relevance_score == unique_jobs_dict[key].relevance_score and not unique_jobs_dict[key].url and job.url): # Prefer job with URL if other has none
                unique_jobs_dict[key] = job
        
        unique_jobs = list(unique_jobs_dict.values())
        
        # Filter out jobs with zero relevance (indicates conflicting terms)
        unique_jobs = [job for job in unique_jobs if job.relevance_score > 0]
        
        # Sort by relevance score (highest first)
        unique_jobs.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top jobs, up to max_total
        final_jobs = unique_jobs[:max_total]
        logger.info(f"Returning {len(final_jobs)} real jobs after deduplication and sorting.")
        
        return final_jobs

    def search_jobs(self, keywords: str, location: str = "", max_results: int = 25) -> List[Dict]:
        """
        Main method to search for jobs across all sources.
        """
        try:
            # Get jobs from all sources
            jobs = self.scrape_all_sources(
                keywords=keywords,
                location=location,
                max_total=max_results
            )
            
            # Convert to dictionaries for JSON response
            return [job.to_dict() for job in jobs]
            
        except Exception as e:
            logger.error(f"Error in search_jobs: {str(e)}")
            return []

    def save_jobs_to_file(self, jobs: List[Dict], filename: str = "jobs.json"):
        """Save jobs to JSON file with proper formatting."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            logger.error(f"Error saving jobs to file: {e}")

    def format_jobs_for_display(self, jobs: List[Dict]) -> str:
        """Format jobs for console display."""
        output = []
        output.append(f"\n{'='*80}")
        output.append(f"Found {len(jobs)} jobs")
        output.append(f"{'='*80}\n")
        
        for i, job in enumerate(jobs, 1):
            output.append(f"{i}. {job['title']} at {job['company']}")
            output.append(f"   Location: {job['location']}")
            output.append(f"   Experience: {job['experience_level']}")
            if job.get('salary_range'):
                output.append(f"   Salary: {job['salary_range']}")
            output.append(f"   Source: {job['source']}")
            output.append(f"   Relevance: {job['relevance_score']}%")
            if job.get('technologies'):
                output.append(f"   Technologies: {', '.join(job['technologies'][:5])}")
            output.append(f"   URL: {job['url']}")
            output.append("")
        
        return "\n".join(output)


# Example usage
if __name__ == "__main__":
    # Initialize the scraper
    scraper = JobScraper()
    
    # Example searches
    print("Starting job search examples...\n")
    
    # Search 1: Python developer jobs
    print("Searching for Python Developer jobs...")
    python_jobs = scraper.search_jobs("python developer", "Remote", max_results=15)
    print(scraper.format_jobs_for_display(python_jobs[:5]))
    scraper.save_jobs_to_file(python_jobs, "python_jobs.json")
    
    print("\n" + "="*80 + "\n")
    
    # Search 2: Data scientist jobs
    print("Searching for Data Scientist jobs...")
    data_jobs = scraper.search_jobs("data scientist", "San Francisco", max_results=10)
    print(scraper.format_jobs_for_display(data_jobs[:3]))
    scraper.save_jobs_to_file(data_jobs, "data_scientist_jobs.json")
    
    print("\n" + "="*80 + "\n")
    
    # Search 3: React developer jobs
    print("Searching for React Developer jobs...")
    react_jobs = scraper.search_jobs("react developer", "", max_results=10)
    print(scraper.format_jobs_for_display(react_jobs[:3]))
    scraper.save_jobs_to_file(react_jobs, "react_jobs.json")
    
    print("\nJob search completed!")