import { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  Heading,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Stack,
  Badge,
  useToast,
  Spinner,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Link,
  Select,
  Grid,
  GridItem,
  Divider,
  Tag,
  Wrap,
  WrapItem
} from '@chakra-ui/react'
import { jobAPI } from '../services/api'
import { storage } from '../services/storage'

function JobSearch() {
  const [keywords, setKeywords] = useState('')
  const [location, setLocation] = useState('')
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedJob, setSelectedJob] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [generatedDocuments, setGeneratedDocuments] = useState(null)
  const { isOpen, onOpen, onClose } = useDisclosure()
  const { isOpen: isSuccessOpen, onOpen: onSuccessOpen, onClose: onSuccessClose } = useDisclosure()
  const toast = useToast()

  const handleSearch = async () => {
    if (!keywords.trim() && !location.trim()) {
      toast({
        title: 'Search Required',
        description: 'Please enter keywords or location to start a search.',
        status: 'info',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setLoading(true)
    setJobs([])
    try {
      const results = await jobAPI.searchJobs(keywords, location)
      setJobs(results)
      if (results.length === 0) {
        toast({
          title: 'No Jobs Found',
          description: 'Try adjusting your search criteria.',
          status: 'info',
          duration: 3000,
          isClosable: true,
        })
      }
    } catch (error) {
      toast({
        title: 'Error Fetching Jobs',
        description: error.message || 'Failed to fetch jobs. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
    setLoading(false)
  }

  const handleGenerateApplication = async (job) => {
    setSelectedJob(job)
    onOpen()
  }

  const confirmGenerate = async () => {
    if (!selectedJob) return
    setGenerating(true)
    try {
      const userInfo = storage.getUserInfo()
      const resumeText = storage.getResume()
      const linkedInData = storage.getLinkedInData()

      if (!userInfo || !resumeText) {
        toast({
          title: 'User Data Missing',
          description: 'Please complete your profile and resume in onboarding first.',
          status: 'warning',
          duration: 5000,
          isClosable: true,
        })
        setGenerating(false)
        return
      }
      
      // Combine all user data sources
      const enrichedUserInfo = {
        ...userInfo,
        resume: resumeText,
        linkedin_data: linkedInData,
        // Add the job info for context
        target_job: {
          title: selectedJob.title,
          company: selectedJob.company,
          description: selectedJob.description,
          technologies: selectedJob.technologies || [],
          experience_level: selectedJob.experience_level
        }
      }

      const resumeResult = await jobAPI.generateResume(selectedJob.description, enrichedUserInfo)
      const coverLetterResult = await jobAPI.generateCoverLetter(selectedJob.description, selectedJob.company, enrichedUserInfo)

      // Store the PDF URLs
      const docs = {
        resumeUrl: resumeResult.url,
        resumeBlob: resumeResult.blob,
        coverLetterUrl: coverLetterResult.url,
        coverLetterBlob: coverLetterResult.blob
      }
      setGeneratedDocuments(docs)

      const applications = JSON.parse(localStorage.getItem('applications') || '[]')
      applications.push({
        id: selectedJob.id + '_' + Date.now(),
        job: selectedJob,
        generatedResumeUrl: resumeResult.url,
        generatedCoverLetterUrl: coverLetterResult.url,
        appliedDate: new Date().toISOString(),
        status: 'Generated'
      })
      localStorage.setItem('applications', JSON.stringify(applications))

      onClose() // Close the generation modal
      onSuccessOpen() // Open the success modal
      
      toast({
        title: 'Application Generated',
        description: 'Resume and cover letter are ready!',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (error) {
      toast({
        title: 'Generation Failed',
        description: error.message || 'Could not generate application documents.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
    setGenerating(false)
  }

  const downloadDocument = (blob, filename) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <Box p={5}>
      <VStack spacing={6} align="stretch">
        <Heading size="xl" textAlign="center">Find Your Next Opportunity</Heading>

        <HStack spacing={4} width="full">
          <Input
            placeholder="Keywords (e.g., Python, React)"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            size="lg"
            flex={1}
          />
          <Input
            placeholder="Location (e.g., Remote, London)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            size="lg"
            flex={1}
          />
        </HStack>
        
        <Button
          colorScheme="blue"
          onClick={handleSearch}
          isLoading={loading}
          size="lg"
          width="full"
        >
          Search Jobs
        </Button>

        {loading ? (
          <VStack justifyContent="center" alignItems="center" height="200px">
            <Spinner size="xl" thickness="4px" color="blue.500" />
            <Text mt={3} fontSize="lg">Searching for jobs...</Text>
          </VStack>
        ) : jobs.length === 0 && !loading ? (
          <Box textAlign="center" py={10}>
            <Text fontSize="xl" color="gray.600">No jobs found matching your criteria. Try broadening your search!</Text>
          </Box>
        ) : (
          <VStack spacing={5} align="stretch">
            {jobs.map((job) => (
              <Card key={job.id} variant="outline" borderWidth="1px" borderRadius="lg" overflow="hidden">
                <CardHeader pb={2}>
                  <HStack justify="space-between" align="flex-start">
                    <Heading size="md">
                      {job.url ? (
                        <Link href={job.url} isExternal color="blue.600" fontWeight="bold">
                          {job.title}
                        </Link>
                      ) : (
                        job.title
                      )}
                    </Heading>
                    <Badge colorScheme={job.source === 'Placeholder (Example)' ? "yellow" : "purple"} fontSize="sm" textTransform="capitalize">
                      {job.source}
                    </Badge>
                  </HStack>
                  <Text fontSize="sm" color="gray.600">{job.company}</Text>
                </CardHeader>
                <CardBody py={3}>
                  <VStack align="stretch" spacing={2.5}>
                    <HStack spacing={3} wrap="wrap">
                      {job.location && <Badge colorScheme="gray">{job.location}</Badge>}
                      {job.job_type && <Badge colorScheme="blue">{job.job_type}</Badge>}
                      {job.experience_level && <Badge colorScheme="green">{job.experience_level}</Badge>}
                    </HStack>
                    
                    {job.salary_range && (
                      <Text fontSize="sm" color="gray.700"><b>Salary:</b> {job.salary_range}</Text>
                    )}
                    
                    <Text fontSize="sm" noOfLines={3}>{job.description}</Text>
                    
                    {job.technologies && job.technologies.length > 0 && (
                      <Box mt={1}>
                        <Text fontSize="xs" color="gray.600" mb={1}>Key Technologies:</Text>
                        <Wrap spacing={2}>
                          {job.technologies.slice(0, 5).map(tech => (
                            <WrapItem key={tech}><Tag size="sm" colorScheme="teal">{tech}</Tag></WrapItem>
                          ))}
                        </Wrap>
                      </Box>
                    )}
                    {job.posted_date && <Text fontSize="xs" color="gray.500" mt={2}>Posted: {job.posted_date}</Text>}
                  </VStack>
                </CardBody>
                <CardFooter pt={2}>
                  <Button
                    colorScheme="teal"
                    variant="solid"
                    onClick={() => handleGenerateApplication(job)}
                  >
                    Generate Application
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </VStack>
        )}
      </VStack>

      {selectedJob && (
        <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Generate Application for: {selectedJob.title}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {generating ? (
                <VStack spacing={4} py={8} alignItems="center">
                  <Spinner size="xl" color="blue.500"/>
                  <Text fontSize="lg">Generating your customized application...</Text>
                  <Text fontSize="sm" color="gray.600">This may take a moment.</Text>
                </VStack>
              ) : (
                <VStack spacing={3} align="stretch">
                  <Text><b>Company:</b> {selectedJob.company}</Text>
                  <Text><b>Location:</b> {selectedJob.location}</Text>
                  <Text><b>Type:</b> {selectedJob.job_type || 'N/A'}</Text>
                  <Text><b>Experience:</b> {selectedJob.experience_level || 'N/A'}</Text>
                  {selectedJob.salary_range && <Text><b>Salary:</b> {selectedJob.salary_range}</Text>}
                  <Text mt={2}><b>Description Snapshot:</b></Text>
                  <Text fontSize="sm" noOfLines={4} p={2} borderWidth="1px" borderColor="gray.200" borderRadius="md">
                    {selectedJob.description}
                  </Text>
                  <Divider my={3}/>
                  <Text fontSize="sm" color="gray.700">
                    Clicking "Confirm & Generate" will use your stored resume and information 
                    to tailor a new resume and cover letter for this specific job.
                  </Text>
                </VStack>
              )}
            </ModalBody>
            <ModalFooter>
              <Button variant='ghost' mr={3} onClick={onClose} isDisabled={generating}>
                Cancel
              </Button>
              <Button 
                colorScheme="blue" 
                onClick={confirmGenerate} 
                isLoading={generating}
                loadingText="Generating..."
              >
                Confirm & Generate
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      )}

      {/* Success Modal */}
      {generatedDocuments && (
        <Modal isOpen={isSuccessOpen} onClose={onSuccessClose} size="lg" isCentered>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Documents Generated Successfully!</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4} align="stretch">
                <Text>Your customized resume and cover letter have been generated as PDFs.</Text>
                
                <HStack spacing={4} justify="center">
                  <Button
                    colorScheme="blue"
                    leftIcon={<Text>📄</Text>}
                    onClick={() => downloadDocument(generatedDocuments.resumeBlob, `resume_${selectedJob.company}_${Date.now()}.pdf`)}
                  >
                    Download Resume
                  </Button>
                  <Button
                    colorScheme="green"
                    leftIcon={<Text>📝</Text>}
                    onClick={() => downloadDocument(generatedDocuments.coverLetterBlob, `cover_letter_${selectedJob.company}_${Date.now()}.pdf`)}
                  >
                    Download Cover Letter
                  </Button>
                </HStack>
                
                <Divider />
                
                <Text fontSize="sm" color="gray.600">
                  You can also view your generated documents in the Applications page.
                </Text>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" onClick={onSuccessClose}>
                Close
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      )}
    </Box>
  )
}

export default JobSearch 