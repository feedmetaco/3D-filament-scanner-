import { useMemo } from 'react'
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom'
import AddSpoolPage from './pages/AddSpoolPage'
import InventoryPage from './pages/InventoryPage'
import ProductDetailPage from './pages/ProductDetailPage'
import SpoolListPage from './pages/SpoolListPage'
import './App.css'

const NavLink = ({ to, label }: { to: string; label: string }) => {
  const location = useLocation()
  const isActive = useMemo(() => location.pathname === to || location.pathname.startsWith(`${to}/`), [location.pathname, to])

  return (
    <Link className={`nav-link ${isActive ? 'active' : ''}`} to={to}>
      {label}
    </Link>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="app-header">
          <div className="logo">3D Filament Inventory</div>
          <nav className="nav-bar">
            <NavLink to="/" label="Inventory" />
            <NavLink to="/spools" label="Spools" />
            <NavLink to="/add-spool" label="Add Spool" />
          </nav>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<InventoryPage />} />
            <Route path="/spools" element={<SpoolListPage />} />
            <Route path="/products/:id" element={<ProductDetailPage />} />
            <Route path="/add-spool" element={<AddSpoolPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
