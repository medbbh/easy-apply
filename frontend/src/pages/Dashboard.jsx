import { useEffect, useState } from 'react'
import {
  Box,
  Grid,
  Heading,
  Text,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  SimpleGrid,
  Card,
  CardBody,
  VStack,
  HStack,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react'
import { jobAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import MatchScore from '../components/MatchScore'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalApplications: 0,
    activeApplications: 0,
    interviewsScheduled: 0,
    matchScore: 0,
  })
  const [recentApplications, setRecentApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const cardBg = useColorModeValue('white', 'gray.700')

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [applications, jobs] = await Promise.all([
          jobAPI.getApplications(),
          jobAPI.getJobs(),
        ])

        // Calculate statistics
        const totalApplications = applications.length
        const activeApplications = applications.filter(
          (app) => app.status === 'active'
        ).length
        const interviewsScheduled = applications.filter(
          (app) => app.status === 'interview'
        ).length

        // Calculate average match score
        const matchScore =
          applications.reduce((acc, app) => acc + (app.matchScore || 0), 0) /
          (totalApplications || 1)

        setStats({
          totalApplications,
          activeApplications,
          interviewsScheduled,
          matchScore: Math.round(matchScore),
        })

        // Get recent applications with job details
        const recentApps = applications
          .slice(0, 5)
          .map((app) => ({
            ...app,
            job: jobs.find((job) => job.id === app.jobId),
          }))
        setRecentApplications(recentApps)
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <Box>
      <Heading mb={6}>Dashboard</Heading>

      {/* Statistics */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Stat
          px={4}
          py={5}
          bg={cardBg}
          shadow="base"
          rounded="lg"
        >
          <StatLabel>Total Applications</StatLabel>
          <StatNumber>{stats.totalApplications}</StatNumber>
          <StatHelpText>
            <StatArrow type="increase" />
            23.36%
          </StatHelpText>
        </Stat>

        <Stat
          px={4}
          py={5}
          bg={cardBg}
          shadow="base"
          rounded="lg"
        >
          <StatLabel>Active Applications</StatLabel>
          <StatNumber>{stats.activeApplications}</StatNumber>
          <StatHelpText>
            <StatArrow type="increase" />
            9.05%
          </StatHelpText>
        </Stat>

        <Stat
          px={4}
          py={5}
          bg={cardBg}
          shadow="base"
          rounded="lg"
        >
          <StatLabel>Interviews Scheduled</StatLabel>
          <StatNumber>{stats.interviewsScheduled}</StatNumber>
          <StatHelpText>
            <StatArrow type="increase" />
            14.05%
          </StatHelpText>
        </Stat>

        <Stat
          px={4}
          py={5}
          bg={cardBg}
          shadow="base"
          rounded="lg"
        >
          <StatLabel>Average Match Score</StatLabel>
          <StatNumber>{stats.matchScore}%</StatNumber>
          <StatHelpText>
            <StatArrow type="increase" />
            5.05%
          </StatHelpText>
        </Stat>
      </SimpleGrid>

      {/* Recent Applications */}
      <Box>
        <Heading size="md" mb={4}>
          Recent Applications
        </Heading>
        <VStack spacing={4} align="stretch">
          {recentApplications.map((application) => (
            <Card key={application.id} bg={cardBg}>
              <CardBody>
                <Grid
                  templateColumns={{ base: '1fr', md: '2fr 1fr' }}
                  gap={4}
                >
                  <VStack align="start" spacing={2}>
                    <Heading size="sm">{application.job?.title}</Heading>
                    <Text fontSize="sm" color="gray.500">
                      {application.job?.company}
                    </Text>
                    <HStack>
                      <Badge
                        colorScheme={
                          application.status === 'active'
                            ? 'green'
                            : application.status === 'interview'
                            ? 'blue'
                            : 'gray'
                        }
                      >
                        {application.status}
                      </Badge>
                      <Text fontSize="sm" color="gray.500">
                        Applied {new Date(application.appliedAt).toLocaleDateString()}
                      </Text>
                    </HStack>
                  </VStack>
                  <Box>
                    <MatchScore
                      score={application.matchScore || 0}
                      label="Job Match"
                    />
                  </Box>
                </Grid>
              </CardBody>
            </Card>
          ))}
        </VStack>
      </Box>
    </Box>
  )
}

export default Dashboard 