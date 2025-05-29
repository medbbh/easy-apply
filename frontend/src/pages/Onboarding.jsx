import { useState } from 'react'
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  Input,
  Textarea,
  useToast,
  FormControl,
  FormLabel,
  FormHelperText
} from '@chakra-ui/react'
import { storage } from '../services/storage'
import { useNavigate } from 'react-router-dom'

function Onboarding() {
  const [step, setStep] = useState(1)
  const [resume, setResume] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [skills, setSkills] = useState('')
  const [experience, setExperience] = useState('')
  const toast = useToast()
  const navigate = useNavigate()

  const handleResumeUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setResume(e.target.result)
      }
      reader.readAsText(file)
    }
  }

  const handleSubmit = () => {
    // Save all user information
    storage.saveResume(resume)
    storage.saveUserInfo({
      skills: skills.split(',').map(s => s.trim()),
      experience: experience
    })
    storage.saveLinkedInData({ url: linkedinUrl })

    toast({
      title: 'Setup Complete',
      description: 'Your information has been saved successfully.',
      status: 'success',
      duration: 3000,
    })

    navigate('/jobs')
  }

  return (
    <Box maxW="600px" mx="auto" p={8}>
      <VStack spacing={8} align="stretch">
        <Heading size="lg">Welcome to Easy Apply</Heading>
        <Text>Let's get your information set up so we can help you find the perfect job.</Text>

        {step === 1 && (
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel>Upload Your Resume</FormLabel>
              <Input
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleResumeUpload}
              />
              <FormHelperText>Upload your current resume in PDF, DOC, or TXT format</FormHelperText>
            </FormControl>

            <FormControl>
              <FormLabel>LinkedIn Profile URL</FormLabel>
              <Input
                type="url"
                placeholder="https://linkedin.com/in/your-profile"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
              />
            </FormControl>

            <Button onClick={() => setStep(2)}>Next</Button>
          </VStack>
        )}

        {step === 2 && (
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel>Your Skills</FormLabel>
              <Textarea
                placeholder="Enter your skills, separated by commas"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
              />
              <FormHelperText>Example: JavaScript, React, Node.js, Python</FormHelperText>
            </FormControl>

            <FormControl>
              <FormLabel>Work Experience</FormLabel>
              <Textarea
                placeholder="Briefly describe your work experience"
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
              />
            </FormControl>

            <Button onClick={() => setStep(1)}>Back</Button>
            <Button colorScheme="blue" onClick={handleSubmit}>
              Complete Setup
            </Button>
          </VStack>
        )}
      </VStack>
    </Box>
  )
}

export default Onboarding 