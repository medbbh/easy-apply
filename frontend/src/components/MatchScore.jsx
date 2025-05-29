import { Box, Progress, Text, VStack } from '@chakra-ui/react'

const MatchScore = ({ score, label }) => {
  const getColor = (score) => {
    if (score >= 80) return 'green'
    if (score >= 60) return 'yellow'
    return 'red'
  }

  return (
    <VStack align="stretch" spacing={2}>
      <Box>
        <Text fontSize="sm" mb={1}>
          {label}
        </Text>
        <Progress
          value={score}
          colorScheme={getColor(score)}
          size="lg"
          borderRadius="full"
          hasStripe
          isAnimated
        />
      </Box>
      <Text fontSize="sm" color="gray.600" textAlign="right">
        {score}% Match
      </Text>
    </VStack>
  )
}

export default MatchScore 