from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProfileBase(BaseModel):
    full_name: str
    skills: str
    experience: str
    education: str

class ProfileCreate(ProfileBase):
    resume_text: str

class Profile(ProfileBase):
    id: int
    user_id: int
    resume_file_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobApplicationBase(BaseModel):
    job_title: str
    company_name: str
    job_description: str
    job_url: str
    status: str = "draft"

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplication(JobApplicationBase):
    id: int
    user_id: int
    profile_id: int
    resume_file_path: Optional[str] = None
    cover_letter_file_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 