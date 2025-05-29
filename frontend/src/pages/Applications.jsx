import { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  Heading,
  Text,
  Card,
  CardBody,
  CardFooter,
  Stack,
  Badge,
  Button,
  HStack,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure
} from '@chakra-ui/react'

function Applications() {
  const [applications, setApplications] = useState([])
  const [selectedApplication, setSelectedApplication] = useState(null)
  const { isOpen, onOpen, onClose } = useDisclosure()
  const toast = useToast()

  useEffect(() => {
    const storedApplications = JSON.parse(localStorage.getItem('applications') || '[]')
    setApplications(storedApplications)
  }, [])

  const handleViewDocuments = (application) => {
    setSelectedApplication(application)
    onOpen()
  }

  const handleDownload = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'generated':
        return 'blue'
      case 'applied':
        return 'green'
      case 'interview':
        return 'purple'
      case 'rejected':
        return 'red'
      default:
        return 'gray'
    }
  }

  return (
    <Box>
      <VStack spacing={8} align="stretch">
        <Heading size="lg">Your Applications</Heading>

        {applications.length === 0 ? (
          <Text>No applications yet. Start by searching for jobs!</Text>
        ) : (
          <Stack spacing={4}>
            {applications.map((app) => (
              <Card key={app.id}>
                <CardBody>
                  <VStack align="stretch" spacing={3}>
                    <Heading size="md">{app.job.title}</Heading>
                    <Text color="gray.600">{app.job.company}</Text>
                    <HStack>
                      <Badge colorScheme="blue">{app.job.type}</Badge>
                      <Badge colorScheme="green">{app.job.location}</Badge>
                      <Badge colorScheme={getStatusColor(app.status)}>
                        {app.status}
                      </Badge>
                    </HStack>
                    <Text fontSize="sm" color="gray.500">
                      Generated on {new Date(app.date).toLocaleDateString()}
                    </Text>
                  </VStack>
                </CardBody>
                <CardFooter>
                  <HStack spacing={4}>
                    <Button
                      colorScheme="blue"
                      onClick={() => handleViewDocuments(app)}
                    >
                      View Documents
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleDownload(app.resume, 'resume.txt')}
                    >
                      Download Resume
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleDownload(app.coverLetter, 'cover-letter.txt')}
                    >
                      Download Cover Letter
                    </Button>
                  </HStack>
                </CardFooter>
              </Card>
            ))}
          </Stack>
        )}
      </VStack>

      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Application Documents</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedApplication && (
              <VStack spacing={6} align="stretch" pb={6}>
                <Box>
                  <Heading size="sm" mb={2}>Customized Resume</Heading>
                  <Text whiteSpace="pre-wrap">{selectedApplication.resume}</Text>
                </Box>
                <Box>
                  <Heading size="sm" mb={2}>Cover Letter</Heading>
                  <Text whiteSpace="pre-wrap">{selectedApplication.coverLetter}</Text>
                </Box>
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default Applications 