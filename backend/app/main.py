from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import os
from datetime import datetime
from .job_scraper import JobScraper
from .latex_service import LaTeXService
from .ai_service import AIService
import io

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

# Initialize services
job_scraper = JobScraper()
latex_service = LaTeXService()
ai_service = AIService()

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
    max_results: int = Query(25, description="Maximum number of results to return", ge=1, le=50)
):
    """
    Search for jobs using various criteria.
    The job scraper will attempt to find jobs from LinkedIn, Indeed, and RemoteOK.
    Results are deduplicated and sorted by relevance.
    """
    try:
        print(f"Received search request: Keywords='{keywords}', Location='{location}', MaxResults={max_results}")
        # Pass parameters to the scraper method
        jobs = job_scraper.search_jobs(
            keywords=keywords, 
            location=location, 
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
    try:
        # Debug logging
        print(f"Received user_info type: {type(request.user_info)}")
        print(f"Received user_info: {request.user_info}")
        
        # Ensure user_info is a dict
        user_info = request.user_info
        if isinstance(user_info, str):
            import json
            try:
                user_info = json.loads(user_info)
            except:
                user_info = {"resume": user_info}
        
        # Extract structured information from resume text if available
        extracted_info = {}
        resume_text = user_info.get('resume', '')
        if resume_text and hasattr(ai_service, 'extract_resume_info'):
            try:
                print("Extracting structured info from resume text...")
                extracted_info = ai_service.extract_resume_info(resume_text)
                print(f"Extracted info keys: {list(extracted_info.keys())}")
            except Exception as e:
                print(f"Failed to extract resume info: {e}")
                extracted_info = {}
        
        # Merge all data sources with priority: user_info > linkedin_data > extracted_info
        parsed_user_info = {
            'full_name': user_info.get('full_name') or user_info.get('name') or extracted_info.get('full_name', 'Your Name'),
            'email': user_info.get('email') or extracted_info.get('email', 'email@example.com'),
            'phone': user_info.get('phone') or extracted_info.get('phone', ''),
            'linkedin': user_info.get('linkedin') or extracted_info.get('linkedin', ''),
            'github': user_info.get('github') or extracted_info.get('github', ''),
            'address': user_info.get('address') or extracted_info.get('address', ''),
            'summary': user_info.get('summary') or extracted_info.get('summary', ''),
            'education': user_info.get('education') or extracted_info.get('education', []),
            'experience': user_info.get('experience') or extracted_info.get('experience', []),
            'skills': user_info.get('skills') or extracted_info.get('skills', {}),
            'projects': user_info.get('projects') or extracted_info.get('projects', []),
            'certifications': user_info.get('certifications') or extracted_info.get('certifications', []),
            'resume': resume_text
        }
        
        # Process LinkedIn data if available
        linkedin_data = user_info.get('linkedin_data', {})
        if linkedin_data:
            # Override with LinkedIn data where available
            if linkedin_data.get('name'):
                parsed_user_info['full_name'] = linkedin_data['name']
            if linkedin_data.get('headline'):
                parsed_user_info['linkedin_headline'] = linkedin_data['headline']
            # Add more LinkedIn fields as needed
        
        # Get job-specific customizations from AI
        ai_customized_content = {}
        target_job = user_info.get('target_job', {})
        
        # Generate a tailored professional summary
        if hasattr(ai_service, 'generate_professional_summary'):
            try:
                print("Generating tailored professional summary...")
                tailored_summary = ai_service.generate_professional_summary(
                    parsed_user_info,
                    request.job_description,
                    target_job.get('company', 'the company')
                )
                ai_customized_content['summary'] = tailored_summary
                print(f"Generated summary: {tailored_summary[:100]}...")
            except Exception as e:
                print(f"Failed to generate professional summary: {e}")
        
        # If no AI summary, try to extract from customized resume
        if not ai_customized_content.get('summary') and hasattr(ai_service, 'customize_resume') and resume_text:
            try:
                customized_text = ai_service.customize_resume(
                    resume_text,
                    request.job_description
                )
                
                # Extract a professional summary tailored to this job
                if isinstance(customized_text, str):
                    lines = customized_text.split('\n')
                    # Find a summary or objective section
                    for i, line in enumerate(lines):
                        if 'summary' in line.lower() or 'objective' in line.lower():
                            if i + 1 < len(lines):
                                ai_customized_content['summary'] = lines[i + 1].strip()
                                break
                    if not ai_customized_content.get('summary') and lines:
                        ai_customized_content['summary'] = lines[0].strip()
            except Exception as e:
                print(f"AI customization failed: {e}")
        
        print(f"Final parsed_user_info keys: {list(parsed_user_info.keys())}")
        print(f"AI customized content: {ai_customized_content}")
        
        # Generate LaTeX resume
        try:
            latex_content = latex_service.generate_resume_latex(
                user_info=parsed_user_info,
                job_specific_content=ai_customized_content
            )
        except Exception as latex_error:
            print(f"LaTeX generation error: {latex_error}")
            print(f"Error type: {type(latex_error)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise latex_error
        
        # Compile to PDF
        pdf_bytes = latex_service.compile_latex_to_pdf(latex_content)
        
        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
    except Exception as e:
        # If LaTeX compilation fails, try fallback method
        if "LaTeX compiler" in str(e) or "LaTeX compilation failed" in str(e):
            try:
                print(f"LaTeX compilation failed, using fallback: {e}")
                pdf_bytes = latex_service.generate_pdf_fallback(parsed_user_info, 'resume')
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    }
                )
            except Exception as fallback_error:
                print(f"Fallback PDF generation also failed: {fallback_error}")
                raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(fallback_error)}")
        else:
            print(f"Error generating resume: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate resume: {str(e)}")

@app.post("/jobs/generate-cover-letter")
async def generate_cover_letter(request: DocumentRequest):
    try:
        # Debug logging
        print(f"Received user_info type: {type(request.user_info)}")
        
        # Ensure user_info is a dict
        user_info = request.user_info
        if isinstance(user_info, str):
            import json
            try:
                user_info = json.loads(user_info)
            except:
                user_info = {"resume": user_info}
        
        # Extract structured information from resume text if available
        extracted_info = {}
        resume_text = user_info.get('resume', '')
        if resume_text and hasattr(ai_service, 'extract_resume_info'):
            try:
                print("Extracting structured info from resume text for cover letter...")
                extracted_info = ai_service.extract_resume_info(resume_text)
            except Exception as e:
                print(f"Failed to extract resume info: {e}")
                extracted_info = {}
        
        # Merge all data sources
        parsed_user_info = {
            'full_name': user_info.get('full_name') or user_info.get('name') or extracted_info.get('full_name', 'Your Name'),
            'email': user_info.get('email') or extracted_info.get('email', 'email@example.com'),
            'phone': user_info.get('phone') or extracted_info.get('phone', ''),
            'address': user_info.get('address') or extracted_info.get('address', 'Your Address'),
            'linkedin': user_info.get('linkedin') or extracted_info.get('linkedin', ''),
            'github': user_info.get('github') or extracted_info.get('github', ''),
            'experience': user_info.get('experience') or extracted_info.get('experience', []),
            'skills': user_info.get('skills') or extracted_info.get('skills', {}),
            'resume': resume_text
        }
        
        # Process LinkedIn data if available
        linkedin_data = user_info.get('linkedin_data', {})
        if linkedin_data and linkedin_data.get('name'):
            parsed_user_info['full_name'] = linkedin_data['name']
        
        # Get target job info
        target_job = user_info.get('target_job', {})
        
        # Extract job info
        job_info = {
            'title': target_job.get('title') or request.job_description.split('\n')[0] if request.job_description else 'Position',
            'company': target_job.get('company') or user_info.get('target_company', 'Company')
        }
        
        # Generate cover letter content using AI with full context
        cover_letter_content = "I am writing to express my strong interest in this position..."
        if hasattr(ai_service, 'generate_cover_letter') and parsed_user_info.get('resume'):
            try:
                # Create an enhanced prompt with all user info
                enhanced_resume = f"""
                Name: {parsed_user_info['full_name']}
                Email: {parsed_user_info['email']}
                Phone: {parsed_user_info['phone']}
                
                Experience: {len(parsed_user_info.get('experience', []))} positions
                Key Skills: {', '.join(list(parsed_user_info.get('skills', {}).values())[0][:5]) if parsed_user_info.get('skills') else 'Various technical skills'}
                
                Full Resume:
                {parsed_user_info['resume']}
                """
                
                cover_letter_content = ai_service.generate_cover_letter(
                    enhanced_resume,
                    request.job_description,
                    job_info['company']
                )
            except Exception as e:
                print(f"AI cover letter generation failed: {e}")
        
        # Generate LaTeX cover letter
        latex_content = latex_service.generate_cover_letter_latex(
            user_info=parsed_user_info,
            job_info=job_info,
            cover_letter_content=cover_letter_content
        )
        
        # Compile to PDF
        pdf_bytes = latex_service.compile_latex_to_pdf(latex_content)
        
        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
    except Exception as e:
        # If LaTeX compilation fails, try fallback method
        if "LaTeX compiler" in str(e) or "LaTeX compilation failed" in str(e):
            try:
                print(f"LaTeX compilation failed, using fallback: {e}")
                pdf_bytes = latex_service.generate_pdf_fallback({
                    'user_info': parsed_user_info,
                    'job_info': job_info,
                    'content': cover_letter_content
                }, 'cover_letter')
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    }
                )
            except Exception as fallback_error:
                print(f"Fallback PDF generation also failed: {fallback_error}")
                raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(fallback_error)}")
        else:
            print(f"Error generating cover letter: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 