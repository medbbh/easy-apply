const API_BASE_URL = 'http://127.0.0.1:8000'

export const jobAPI = {
  async searchJobs(keywords, location = '') {
    const response = await fetch(
      `${API_BASE_URL}/jobs/search?keywords=${encodeURIComponent(keywords)}&location=${encodeURIComponent(location)}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch jobs')
    }
    return response.json()
  },

  async generateResume(jobDescription, userInfo) {
    const response = await fetch(`${API_BASE_URL}/jobs/generate-resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_description: jobDescription,
        user_info: userInfo,
      }),
    })
    if (!response.ok) {
      throw new Error('Failed to generate resume')
    }
    return response.text()
  },

  async generateCoverLetter(jobDescription, companyName, userInfo) {
    const response = await fetch(`${API_BASE_URL}/jobs/generate-cover-letter`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_description: jobDescription,
        user_info: userInfo,
      }),
    })
    if (!response.ok) {
      throw new Error('Failed to generate cover letter')
    }
    return response.text()
  },

  async analyzeJobFit(jobDescription, userInfo) {
    const response = await fetch(`${API_BASE_URL}/analyze/job-fit`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_description: jobDescription,
        user_info: userInfo,
      }),
    })
    if (!response.ok) {
      throw new Error('Failed to analyze job fit')
    }
    return response.json()
  }
} 