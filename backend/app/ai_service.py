from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
from dotenv import load_dotenv
from typing import Dict, List
import json

load_dotenv()

class AIService:
    def __init__(self):
        self.client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
        self.model = "mistral-large-latest"

    def customize_resume(self, resume_text: str, job_description: str) -> str:
        prompt = f"""
        Please customize the following resume to better match the job description.
        Focus on highlighting relevant skills and experiences.
        Keep the same format but adjust the content to align with the job requirements.

        Job Description:
        {job_description}

        Original Resume:
        {resume_text}

        Customized Resume:
        """

        messages = [
            ChatMessage(role="user", content=prompt)
        ]

        response = self.client.chat(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content

    def generate_cover_letter(self, resume_text: str, job_description: str, company_name: str) -> str:
        prompt = f"""
        Please write a compelling cover letter based on the following resume and job description.
        The cover letter should be professional, highlight relevant skills, and show enthusiasm for the position.

        Company: {company_name}

        Job Description:
        {job_description}

        Resume:
        {resume_text}

        Cover Letter:
        """

        messages = [
            ChatMessage(role="user", content=prompt)
        ]

        response = self.client.chat(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content

    def analyze_job_fit(self, resume_text: str, job_description: str) -> Dict:
        prompt = f"""
        Please analyze how well the resume matches the job description.
        Provide a score from 0-100 and specific recommendations for improvement.

        Job Description:
        {job_description}

        Resume:
        {resume_text}

        Analysis:
        """

        messages = [
            ChatMessage(role="user", content=prompt)
        ]

        response = self.client.chat(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        return {
            "analysis": response.choices[0].message.content,
            "score": self._extract_score(response.choices[0].message.content)
        }

    def _extract_score(self, analysis: str) -> int:
        # Simple score extraction - you might want to make this more sophisticated
        try:
            # Look for a number between 0 and 100 in the text
            import re
            numbers = re.findall(r'\b(?:100|[1-9]?[0-9])\b', analysis)
            if numbers:
                return int(numbers[0])
            return 50  # Default score if no number found
        except:
            return 50  # Default score if extraction fails

    def extract_resume_info(self, resume_text: str) -> Dict:
        """Extract structured information from resume text."""
        prompt = f"""
        Extract structured information from the following resume text. 
        Return a JSON object with the following structure:
        {{
            "full_name": "extracted name",
            "email": "extracted email",
            "phone": "extracted phone",
            "linkedin": "extracted linkedin url or username",
            "github": "extracted github url or username",
            "address": "extracted address",
            "summary": "professional summary or objective",
            "education": [
                {{"degree": "degree name", "school": "school name", "dates": "dates attended", "gpa": "if mentioned"}}
            ],
            "experience": [
                {{"title": "job title", "company": "company name", "dates": "employment dates", "technologies": "tech stack used", "bullets": ["achievement 1", "achievement 2"]}}
            ],
            "skills": {{
                "Languages": ["Python", "JavaScript", etc],
                "Frameworks": ["React", "Django", etc],
                "Databases": ["PostgreSQL", "MongoDB", etc],
                "Tools": ["Git", "Docker", etc]
            }},
            "projects": [
                {{"name": "project name", "technologies": "tech used", "date": "date", "bullets": ["description", "achievements"]}}
            ],
            "certifications": [
                {{"name": "certification name", "issuer": "issuing organization", "date": "date"}}
            ]
        }}
        
        If any field is not found in the resume, use appropriate empty values (empty string for strings, empty arrays for arrays, empty objects for objects).
        Make sure to categorize skills appropriately.
        
        Resume text:
        {resume_text}
        
        JSON output:
        """

        messages = [
            ChatMessage(role="user", content=prompt)
        ]

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=2000
            )
            
            # Extract JSON from response
            response_text = response.choices[0].message.content
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # If no JSON found, return empty structure
                return self._empty_resume_structure()
                
        except Exception as e:
            print(f"Error extracting resume info: {e}")
            return self._empty_resume_structure()
    
    def _empty_resume_structure(self) -> Dict:
        """Return empty resume structure."""
        return {
            "full_name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "address": "",
            "summary": "",
            "education": [],
            "experience": [],
            "skills": {},
            "projects": [],
            "certifications": []
        }

    def generate_professional_summary(self, user_info: Dict, job_description: str, company: str) -> str:
        """Generate a professional summary tailored to a specific job."""
        prompt = f"""
        Create a compelling professional summary (3-4 lines) for a resume tailored to this specific job.
        
        User background:
        - Name: {user_info.get('full_name', 'Professional')}
        - Current experience: {user_info.get('experience', [{}])[0].get('title', '')} if any
        - Skills: {', '.join(user_info.get('skills', {}).get('Languages', [])[:3] + user_info.get('skills', {}).get('Frameworks', [])[:3])}
        - Years of experience: {user_info.get('years_experience', 'several years')}
        
        Target Job:
        Company: {company}
        Job Description: {job_description[:500]}...
        
        Guidelines:
        - Highlight relevant skills that match the job requirements
        - Mention specific technologies if they align with the job
        - Show enthusiasm for the company/role
        - Be concise and impactful
        - Use action words and quantify achievements where possible
        
        Professional Summary:
        """
        
        messages = [
            ChatMessage(role="user", content=prompt)
        ]
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            summary = response.choices[0].message.content.strip()
            # Remove any quotation marks or "Professional Summary:" prefix
            summary = summary.replace('"', '').replace("'", '')
            if summary.lower().startswith('professional summary:'):
                summary = summary[20:].strip()
            
            return summary
            
        except Exception as e:
            print(f"Error generating professional summary: {e}")
            return "Experienced professional seeking to contribute technical expertise and drive innovation in a dynamic environment." 