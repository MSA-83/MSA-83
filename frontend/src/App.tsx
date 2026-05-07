import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import ChatWebSocket from './pages/ChatWebSocket'
import Memory from './pages/Memory'
import Agents from './pages/Agents'
import Billing from './components/Billing/Billing'
import Login from './pages/Login'
import OAuthCallback from './pages/OAuthCallback'
import Admin from './pages/Admin'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<OAuthCallback />} />
      <Route path="/" element={<Layout><Dashboard /></Layout>} />
      <Route path="/chat" element={<Layout><Chat /></Layout>} />
      <Route path="/chat/ws" element={<Layout><ChatWebSocket /></Layout>} />
      <Route path="/memory" element={<Layout><Memory /></Layout>} />
      <Route path="/agents" element={<Layout><Agents /></Layout>} />
      <Route path="/billing" element={<Layout><Billing /></Layout>} />
      <Route path="/admin" element={<Layout><Admin /></Layout>} />
      <Route path="/settings" element={<Layout><Settings /></Layout>} />
    </Routes>
  )
}

export default App
