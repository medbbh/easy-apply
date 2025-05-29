import { ChakraProvider, Box } from '@chakra-ui/react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { storage } from './services/storage'

// Components
import Navbar from './components/Navbar'

// Pages
import Onboarding from './pages/Onboarding'
import JobSearch from './pages/JobSearch'
import Applications from './pages/Applications'

function App() {
  const [hasUserInfo, setHasUserInfo] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const userInfo = storage.getUserInfo()
    setHasUserInfo(!!userInfo)
    setLoading(false)
  }, [])

  if (loading) {
    return null
  }

  return (
    <ChakraProvider>
      <Router>
        <Box minH="100vh" bg="gray.50">
          {hasUserInfo && <Navbar />}
          <Box maxW="1200px" mx="auto" px={4} py={8}>
            <Routes>
              <Route 
                path="/" 
                element={hasUserInfo ? <Navigate to="/jobs" /> : <Onboarding />} 
              />
              <Route 
                path="/jobs" 
                element={hasUserInfo ? <JobSearch /> : <Navigate to="/" />} 
              />
              <Route 
                path="/applications" 
                element={hasUserInfo ? <Applications /> : <Navigate to="/" />} 
              />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ChakraProvider>
  )
}

export default App 