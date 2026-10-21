import { Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from './components/layout/AppLayout'
import ComingSoonPage from './pages/ComingSoonPage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import { navItems } from './navigation'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route element={<AppLayout />}>
        {navItems.map(({ to, label }) => (
          <Route key={to} path={to} element={<ComingSoonPage title={label} />} />
        ))}
        <Route path="/app" element={<Navigate to="/annuaire" replace />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
