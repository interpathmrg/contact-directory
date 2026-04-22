import React from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Navbar from './Navbar';

interface Props {
  children: React.ReactNode;
}

export default function Layout({ children }: Props) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-screen-xl w-full mx-auto px-4 py-6">
        {children}
      </main>
      <ToastContainer position="top-right" autoClose={4000} hideProgressBar={false} />
    </div>
  );
}
