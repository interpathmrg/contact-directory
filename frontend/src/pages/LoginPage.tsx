import React, { useEffect, useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const errParam = searchParams.get('error');
    if (errParam === 'sin_acceso') {
      setError('Tu cuenta no tiene acceso a esta aplicación. Contacta a un administrador.');
    } else if (errParam) {
      setError('Ocurrió un error durante la autenticación. Intenta de nuevo.');
    }
  }, [searchParams]);

  if (!isLoading && isAuthenticated) return <Navigate to="/contacts" replace />;

  const handleLogin = async () => {
    setIsRedirecting(true);
    setError(null);
    try {
      await login();
    } catch {
      setError('No se pudo conectar con el servidor. Intenta de nuevo.');
      setIsRedirecting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 to-primary-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
        {/* Logo / Ícono */}
        <div className="text-6xl mb-4">📋</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Directorio Corporativo</h1>
        <p className="text-gray-500 text-sm mb-8">
          Accede con tu cuenta de Microsoft corporativa
        </p>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm text-left">
            {error}
          </div>
        )}

        <button
          onClick={handleLogin}
          disabled={isRedirecting || isLoading}
          className="w-full flex items-center justify-center gap-3 bg-[#0078d4] hover:bg-[#106ebe] text-white font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isRedirecting ? (
            <>
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Redirigiendo a Microsoft&hellip;
            </>
          ) : (
            <>
              {/* Microsoft logo SVG */}
              <svg width="20" height="20" viewBox="0 0 21 21" fill="none">
                <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
              </svg>
              Iniciar sesión con Microsoft
            </>
          )}
        </button>

        <p className="mt-6 text-xs text-gray-400">
          Solo usuarios con cuenta autorizada pueden acceder.
        </p>
      </div>
    </div>
  );
}
