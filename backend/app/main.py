from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
from .job_scraper import JobScraper

app = FastAPI(
    title="Easy Apply API",
    description="API for job scraping and AI-powered application assistance.",
    version="0.2.0"
)

# Configure CORS
origins = [
    "http://localhost:3000", # React frontend
    "http://localhost:5173", # Vite React frontend
    # Add any other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize job scraper
job_scraper = JobScraper()

class JobSearchParams(BaseModel):
    keywords: str
    location: Optional[str] = None

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    type: str
    description: str
    requirements: List[str]
    source: str

class DocumentRequest(BaseModel):
    job_description: str
    user_info: dict

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Job Search API"}

@app.get("/jobs/search", response_model=List[Dict])
async def search_jobs(
    keywords: str = Query(..., description="Keywords to search for jobs (e.g., python developer)"),
    location: Optional[str] = Query(None, description="Location to search for jobs (e.g., Remote, London)"),
    job_type: Optional[str] = Query(None, description="Filter by job type (e.g., Full-time, Contract)"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level (e.g., Mid-level, Senior)"),
    max_results: int = Query(25, description="Maximum number of results to return", ge=1, le=50)
):
    """
    Search for jobs using various criteria.
    The job scraper will attempt to find jobs from LinkedIn, Indeed, and RemoteOK.
    Results are deduplicated and sorted by relevance.
    """
    try:
        print(f"Received search request: Keywords='{keywords}', Location='{location}', JobType='{job_type}', Experience='{experience_level}', MaxResults={max_results}")
        # Pass the new filters to the scraper method
        jobs = job_scraper.search_jobs(
            keywords=keywords, 
            location=location, 
            job_type_filter=job_type, 
            experience_filter=experience_level, 
            max_results=max_results
        )
        if not jobs:
            print("No jobs found by scraper.")
        return jobs
    except Exception as e:
        print(f"Error during job search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search jobs: {str(e)}")

@app.post("/jobs/generate-resume")
async def generate_resume(request: DocumentRequest):
    # Mock resume generation
    resume = f"""
    CUSTOMIZED RESUME
    ================
    
    {request.user_info.get('full_name', '')}
    {request.user_info.get('title', '')}
    {request.user_info.get('location', '')}
    
    SKILLS
    ------
    {', '.join(request.user_info.get('skills', []))}
    
    EXPERIENCE
    ----------
    {request.user_info.get('experience', '')}
    
    Customized for: {request.job_description[:100]}...
    """
    return resume

@app.post("/jobs/generate-cover-letter")
async def generate_cover_letter(request: DocumentRequest):
    # Mock cover letter generation
    cover_letter = f"""
    Dear Hiring Manager,
    
    I am writing to express my interest in the position. With my background in {', '.join(request.user_info.get('skills', [])[:3])}, 
    I believe I would be a great fit for this role.
    
    {request.user_info.get('experience', '')}
    
    I am excited about the opportunity to contribute to your team and would welcome the chance to discuss how my skills 
    and experience align with your needs.
    
    Best regards,
    {request.user_info.get('full_name', '')}
    """
    return cover_letter

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 