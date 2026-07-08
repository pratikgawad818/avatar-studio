import { Box, Button, Card, CardContent, Grid, TextField, Typography, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { useState, useEffect } from 'react'
import axios from 'axios'

interface Project {
  id: string
  name: string
  description?: string
  created_at: string
}

const Projects = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [open, setOpen] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [projectDesc, setProjectDesc] = useState('')

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const response = await axios.get('/api/projects')
      setProjects(response.data || [])
    } catch (error) {
      console.error('Error fetching projects:', error)
    }
  }

  const handleCreate = async () => {
    try {
      await axios.post('/api/projects', {
        name: projectName,
        description: projectDesc,
      })
      setProjectName('')
      setProjectDesc('')
      setOpen(false)
      fetchProjects()
    } catch (error) {
      console.error('Error creating project:', error)
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Projects
        </Typography>
        <Button variant="contained" onClick={() => setOpen(true)}>
          New Project
        </Button>
      </Box>

      <Grid container spacing={2}>
        {projects.map((project) => (
          <Grid item xs={12} sm={6} md={4} key={project.id}>
            <Card sx={{ cursor: 'pointer', '&:hover': { transform: 'translateY(-4px)', boxShadow: 3 }, transition: 'all 0.2s' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {project.name}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  {project.description}
                </Typography>
                <Typography variant="caption" sx={{ mt: 2, display: 'block' }}>
                  Created: {new Date(project.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent sx={{ minWidth: 400, pt: 2 }}>
          <TextField
            fullWidth
            label="Project Name"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={projectDesc}
            onChange={(e) => setProjectDesc(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleCreate} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Projects
