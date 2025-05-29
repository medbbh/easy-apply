const STORAGE_KEYS = {
  USER_INFO: 'user_info',
  RESUME: 'user_resume',
  LINKEDIN: 'linkedin_data'
}

export const storage = {
  saveUserInfo: (info) => {
    localStorage.setItem(STORAGE_KEYS.USER_INFO, JSON.stringify(info))
  },

  getUserInfo: () => {
    const data = localStorage.getItem(STORAGE_KEYS.USER_INFO)
    return data ? JSON.parse(data) : null
  },

  saveResume: (resumeText) => {
    localStorage.setItem(STORAGE_KEYS.RESUME, resumeText)
  },

  getResume: () => {
    return localStorage.getItem(STORAGE_KEYS.RESUME)
  },

  saveLinkedInData: (data) => {
    localStorage.setItem(STORAGE_KEYS.LINKEDIN, JSON.stringify(data))
  },

  getLinkedInData: () => {
    const data = localStorage.getItem(STORAGE_KEYS.LINKEDIN)
    return data ? JSON.parse(data) : null
  },

  clearAll: () => {
    localStorage.removeItem(STORAGE_KEYS.USER_INFO)
    localStorage.removeItem(STORAGE_KEYS.RESUME)
    localStorage.removeItem(STORAGE_KEYS.LINKEDIN)
  }
} 