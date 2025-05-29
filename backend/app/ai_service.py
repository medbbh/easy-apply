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