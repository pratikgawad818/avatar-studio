import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Container, Box } from '@mui/material'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Generator from './pages/Generator'
import Projects from './pages/Projects'
import Settings from './pages/Settings'

function App() {
  return (
    <Router>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Navbar />
        <Container maxWidth="lg" sx={{ flex: 1, py: 4 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/generate" element={<Generator />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Container>
      </Box>
    </Router>
  )
}

export default App
