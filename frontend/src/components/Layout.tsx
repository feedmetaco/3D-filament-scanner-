import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen pb-24">
      {/* Floating Header */}
      <header className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] max-w-md">
        <div className="glass rounded-3xl shadow-2xl shadow-purple-500/10 p-1">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Filament
              </h1>
            </div>
            <div className="flex gap-1">
              <Link
                to="/scanner"
                className={`px-4 py-2 rounded-xl font-semibold text-sm transition-all ${
                  isActive('/scanner')
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-purple-500/30'
                    : 'text-slate-600 hover:bg-white/50'
                }`}
              >
                Scan
              </Link>
              <Link
                to="/inventory"
                className={`px-4 py-2 rounded-xl font-semibold text-sm transition-all ${
                  isActive('/inventory')
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-purple-500/30'
                    : 'text-slate-600 hover:bg-white/50'
                }`}
              >
                Stock
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content with top padding for floating header */}
      <main className="pt-28 px-4 max-w-md mx-auto">
        <div className="animate-in">
          {children}
        </div>
      </main>
    </div>
  );
}
