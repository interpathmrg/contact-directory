import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium px-3 py-2 rounded-md transition-colors ${
      isActive
        ? 'bg-primary-700 text-white'
        : 'text-primary-100 hover:bg-primary-700 hover:text-white'
    }`;

  return (
    <nav className="bg-primary-800 shadow-md">
      <div className="max-w-screen-xl mx-auto px-4 flex items-center justify-between h-14">
        {/* Logo */}
        <Link to="/" className="text-white font-bold text-lg tracking-tight">
          📋 Directorio Corporativo
        </Link>

        {isAuthenticated && (
          <>
            {/* Nav links */}
            <div className="flex items-center gap-1">
              <NavLink to="/contacts" className={navLinkClass}>Contactos</NavLink>
              <NavLink to="/labels" className={navLinkClass}>Etiquetas</NavLink>
              {user?.is_admin && (
                <>
                  <NavLink to="/import" className={navLinkClass}>Importar / Exportar</NavLink>
                  <NavLink to="/admin" className={navLinkClass}>Administración</NavLink>
                </>
              )}
            </div>

            {/* User menu */}
            <div className="flex items-center gap-3">
              <span className="text-primary-200 text-sm hidden sm:block">
                {user?.name}
                <span className="ml-2 text-xs bg-primary-600 text-white px-2 py-0.5 rounded-full">
                  {user?.role}
                </span>
              </span>
              <button onClick={handleLogout} className="text-primary-200 hover:text-white text-sm transition-colors">
                Salir
              </button>
            </div>
          </>
        )}
      </div>
    </nav>
  );
}
