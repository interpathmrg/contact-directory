import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { AuthProvider } from './hooks/useAuth';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/common/Layout';
import LoadingSpinner from './components/common/LoadingSpinner';

// Lazy pages
const LoginPage       = lazy(() => import('./pages/LoginPage'));
const ContactsPage    = lazy(() => import('./pages/ContactsPage'));
const ContactFormPage = lazy(() => import('./pages/ContactFormPage'));
const ImportPage      = lazy(() => import('./pages/ImportPage'));
const LabelsPage      = lazy(() => import('./pages/LabelsPage'));
const AdminPage       = lazy(() => import('./pages/AdminPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 60_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<LoadingSpinner fullScreen />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />

              {/* Rutas protegidas */}
              <Route path="/" element={<ProtectedRoute><Layout><Navigate to="/contacts" replace /></Layout></ProtectedRoute>} />

              <Route path="/contacts" element={
                <ProtectedRoute><Layout><ContactsPage /></Layout></ProtectedRoute>
              } />
              <Route path="/contacts/new" element={
                <ProtectedRoute requireAdmin><Layout><ContactFormPage /></Layout></ProtectedRoute>
              } />
              <Route path="/contacts/:id/edit" element={
                <ProtectedRoute requireAdmin><Layout><ContactFormPage /></Layout></ProtectedRoute>
              } />

              <Route path="/labels" element={
                <ProtectedRoute><Layout><LabelsPage /></Layout></ProtectedRoute>
              } />
              <Route path="/import" element={
                <ProtectedRoute requireAdmin><Layout><ImportPage /></Layout></ProtectedRoute>
              } />
              <Route path="/admin" element={
                <ProtectedRoute requireAdmin><Layout><AdminPage /></Layout></ProtectedRoute>
              } />

              {/* 404 */}
              <Route path="*" element={
                <div className="min-h-screen flex items-center justify-center">
                  <div className="text-center">
                    <h2 className="text-4xl font-bold text-gray-400 mb-2">404</h2>
                    <p className="text-gray-500 mb-4">Página no encontrada</p>
                    <a href="/" className="btn-primary">Ir al inicio</a>
                  </div>
                </div>
              } />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
