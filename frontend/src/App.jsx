import { Box, Container, Heading, Text, VStack } from '@chakra-ui/react'
import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [message, setMessage] = useState('')

  useEffect(() => {
    const fetchMessage = async () => {
      try {
        const response = await axios.get('/api/')
        setMessage(response.data.message)
      } catch (error) {
        console.error('Error fetching message:', error)
        setMessage('Error connecting to the backend')
      }
    }

    fetchMessage()
  }, [])

  return (
    <Container maxW="container.xl" py={10}>
      <VStack spacing={8}>
        <Heading>Easy Apply</Heading>
        <Box p={6} shadow="md" borderRadius="lg" bg="white" w="full">
          <Text fontSize="xl">{message || 'Loading...'}</Text>
        </Box>
      </VStack>
    </Container>
  )
}

export default App 