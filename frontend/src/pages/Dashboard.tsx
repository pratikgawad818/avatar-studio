import { Box, Grid, Card, CardContent, Typography, Button, LinearProgress } from '@mui/material'
import { useEffect, useState } from 'react'
import axios from 'axios'

interface Job {
  id: string
  status: string
  progress: number
  current_step?: string
  created_at: string
}

const Dashboard = () => {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await axios.get('/api/generation/jobs')
        setJobs(response.data.jobs || [])
      } catch (error) {
        console.error('Error fetching jobs:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchJobs()
    const interval = setInterval(fetchJobs, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ backgroundColor: '#334155' }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Videos
              </Typography>
              <Typography variant="h5">{jobs.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ backgroundColor: '#334155' }}>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                In Progress
              </Typography>
              <Typography variant="h5">{jobs.filter(j => j.status === 'running').length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Recent Jobs
          </Typography>
          {loading ? (
            <Typography>Loading...</Typography>
          ) : jobs.length === 0 ? (
            <Card>
              <CardContent>
                <Typography>No videos generated yet.</Typography>
                <Button variant="contained" sx={{ mt: 2 }}>
                  Create Your First Video
                </Button>
              </CardContent>
            </Card>
          ) : (
            jobs.slice(0, 5).map((job) => (
              <Card key={job.id} sx={{ mb: 2 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2">{job.id}</Typography>
                    <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                      {job.status}
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ mb: 2, display: 'block' }}>
                    {job.current_step}
                  </Typography>
                  <LinearProgress variant="determinate" value={job.progress} />
                </CardContent>
              </Card>
            ))
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard
