import { Spinner, Center } from '@chakra-ui/react'

const LoadingSpinner = ({ size = 'xl' }) => {
  return (
    <Center h="100%" w="100%" minH="200px">
      <Spinner
        thickness="4px"
        speed="0.65s"
        emptyColor="gray.200"
        color="blue.500"
        size={size}
      />
    </Center>
  )
}

export default LoadingSpinner 