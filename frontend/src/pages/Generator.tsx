import { Box, Button, Card, CardContent, TextField, Select, MenuItem, FormControlLabel, Checkbox, Typography, LinearProgress, Alert } from '@mui/material'
import { useState } from 'react'
import axios from 'axios'

const Generator = () => {
  const [script, setScript] = useState('')
  const [voiceMode, setVoiceMode] = useState('fast')
  const [avatarId, setAvatarId] = useState('')
  const [voiceId, setVoiceId] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!script || !avatarId || !voiceId) {
      setError('Please fill in all required fields')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/generation/generate', {
        script,
        avatar_id: avatarId,
        voice_id: voiceId,
        voice_mode: voiceMode,
        resolution: '1920x1080',
        aspect_ratio: '16:9',
        subtitles: true,
      })

      setJobId(response.data.id)

      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`/api/generation/jobs/${response.data.id}`)
          setProgress(statusResponse.data.progress)

          if (statusResponse.data.status === 'completed' || statusResponse.data.status === 'failed') {
            clearInterval(pollInterval)
            setLoading(false)
          }
        } catch (err) {
          clearInterval(pollInterval)
        }
      }, 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Generation failed')
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Generate Video
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Card>
        <CardContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
            <TextField
              fullWidth
              label="Script"
              multiline
              rows={6}
              value={script}
              onChange={(e) => setScript(e.target.value)}
              disabled={loading}
              placeholder="Enter your video script here..."
            />

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Select value={avatarId} onChange={(e) => setAvatarId(e.target.value)} disabled={loading}>
                <MenuItem value="">Select Avatar</MenuItem>
                <MenuItem value="avatar1">Avatar 1</MenuItem>
                <MenuItem value="avatar2">Avatar 2</MenuItem>
              </Select>

              <Select value={voiceId} onChange={(e) => setVoiceId(e.target.value)} disabled={loading}>
                <MenuItem value="">Select Voice</MenuItem>
                <MenuItem value="voice1">Voice 1</MenuItem>
                <MenuItem value="voice2">Voice 2</MenuItem>
              </Select>

              <Select value={voiceMode} onChange={(e) => setVoiceMode(e.target.value)} disabled={loading}>
                <MenuItem value="fast">Fast (Edge-TTS)</MenuItem>
                <MenuItem value="clone">Clone (F5-TTS)</MenuItem>
              </Select>

              <FormControlLabel
                control={<Checkbox defaultChecked />}
                label="Add Subtitles"
                disabled={loading}
              />

              <Button
                variant="contained"
                size="large"
                onClick={handleGenerate}
                disabled={loading}
                sx={{ mt: 'auto' }}
              >
                {loading ? 'Generating...' : 'Generate Video'}
              </Button>
            </Box>
          </Box>

          {loading && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="caption">Progress: {progress}%</Typography>
              <LinearProgress variant="determinate" value={progress} sx={{ mt: 1 }} />
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

export default Generator
