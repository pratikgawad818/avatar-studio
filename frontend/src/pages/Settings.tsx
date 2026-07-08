import { Box, Card, CardContent, Typography, TextField, Button, Switch, FormControlLabel } from '@mui/material'
import { useState } from 'react'

const Settings = () => {
  const [settings, setSettings] = useState({
    voiceMode: 'fast',
    resolution: '1920x1080',
    subtitles: true,
    autoUpload: false,
  })

  const handleSave = () => {
    // Save settings
    console.log('Settings saved:', settings)
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4, fontWeight: 700 }}>
        Settings
      </Typography>

      <Card>
        <CardContent>
          <Box sx={{ display: 'grid', gap: 2, maxWidth: 500 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mt: 2 }}>
              Generation Defaults
            </Typography>

            <TextField label="Default Resolution" value={settings.resolution} fullWidth />

            <FormControlLabel
              control={<Switch checked={settings.subtitles} />}
              label="Enable Subtitles by Default"
            />

            <FormControlLabel
              control={<Switch checked={settings.autoUpload} />}
              label="Auto-upload to Cloud"
            />

            <Button variant="contained" onClick={handleSave} sx={{ mt: 2 }}>
              Save Settings
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Settings
