import { AppBar, Toolbar, Typography, Button, Box, Menu, MenuItem } from '@mui/material'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import MenuIcon from '@mui/icons-material/Menu'
import { useState } from 'react'

const Navbar = () => {
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleNavigate = (path: string) => {
    navigate(path)
    handleClose()
  }

  return (
    <AppBar position="sticky" sx={{ backgroundColor: '#1e293b', borderBottom: '1px solid #334155' }}>
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700, cursor: 'pointer' }} onClick={() => navigate('/')}>
          🎬 Avatar Studio
        </Typography>
        <Box sx={{ display: { xs: 'none', sm: 'flex' }, gap: 2 }}>
          <Button color="inherit" component={RouterLink} to="/">
            Dashboard
          </Button>
          <Button color="inherit" component={RouterLink} to="/generate">
            Generate
          </Button>
          <Button color="inherit" component={RouterLink} to="/projects">
            Projects
          </Button>
          <Button color="inherit" component={RouterLink} to="/settings">
            Settings
          </Button>
        </Box>
        <Box sx={{ display: { xs: 'flex', sm: 'none' } }}>
          <Button onClick={handleMenu} color="inherit">
            <MenuIcon />
          </Button>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleClose}>
            <MenuItem onClick={() => handleNavigate('/')}>Dashboard</MenuItem>
            <MenuItem onClick={() => handleNavigate('/generate')}>Generate</MenuItem>
            <MenuItem onClick={() => handleNavigate('/projects')}>Projects</MenuItem>
            <MenuItem onClick={() => handleNavigate('/settings')}>Settings</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar
