import { Box, Flex, Button, useColorMode, Heading } from '@chakra-ui/react'
import { Link as RouterLink } from 'react-router-dom'
import { MoonIcon, SunIcon } from '@chakra-ui/icons'

function Navbar() {
  const { colorMode, toggleColorMode } = useColorMode()

  return (
    <Box bg={colorMode === 'light' ? 'white' : 'gray.800'} px={4} shadow="sm">
      <Flex h={16} alignItems="center" justifyContent="space-between" maxW="1200px" mx="auto">
        <Heading size="md" as={RouterLink} to="/" _hover={{ textDecoration: 'none' }}>
          Easy Apply
        </Heading>

        <Flex alignItems="center" gap={4}>
          <Button as={RouterLink} to="/jobs" variant="ghost">
            Jobs
          </Button>
          <Button as={RouterLink} to="/applications" variant="ghost">
            Applications
          </Button>
          <Button onClick={toggleColorMode} variant="ghost">
            {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
          </Button>
        </Flex>
      </Flex>
    </Box>
  )
}

export default Navbar 