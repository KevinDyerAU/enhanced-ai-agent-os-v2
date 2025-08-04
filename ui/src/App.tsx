import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import MissionControlDashboard from './components/mission_control/MissionControlDashboard'
import AirlockPage from './pages/AirlockPage'
import TrainingValidationPage from './pages/TrainingValidationPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<MissionControlDashboard />} />
          <Route path="/airlock" element={<AirlockPage />} />
          <Route path="/training" element={<TrainingValidationPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
