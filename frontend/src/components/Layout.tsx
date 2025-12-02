import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen font-sans text-text selection:bg-primary selection:text-black relative overflow-hidden">
      
      {/* Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-grid opacity-[0.03] h-full w-full"></div>
        {/* Ambient Glows */}
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-900/10 blur-[100px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-purple-900/10 blur-[100px]"></div>
      </div>

      {/* CRT Overlay */}
      <div className="crt"></div>

      <div className="relative z-10 max-w-md mx-auto min-h-screen flex flex-col pb-24">
        
        {/* Header / Status Bar */}
        <header className="pt-6 px-4 mb-6 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-wider uppercase text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]">
              Fila<span className="text-primary">Scan</span>
            </h1>
            <div className="flex items-center gap-2 text-xs font-mono text-primary/70">
              <span className="inline-block w-2 h-2 bg-primary rounded-full animate-pulse"></span>
              SYSTEM ONLINE
            </div>
          </div>
          <div className="text-right hidden sm:block">
             <div className="text-xs font-mono text-muted">USER: ADMIN</div>
             <div className="text-xs font-mono text-muted">ID: 001-TX</div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 px-4 space-y-6 animate-in">
          {children}
        </main>

        {/* Bottom Navigation */}
        <nav className="fixed bottom-0 left-0 right-0 bg-surface/90 backdrop-blur-md border-t border-white/10 z-40 pb-safe">
          <div className="flex justify-around items-center h-16 max-w-md mx-auto">
            <Link 
              to="/scanner" 
              className={`flex flex-col items-center gap-1 p-2 group relative transition-colors ${isActive('/scanner') ? 'text-primary' : 'text-muted hover:text-white'}`}
            >
              {isActive('/scanner') && (
                <div className="absolute -top-[1px] left-0 right-0 h-[2px] bg-primary shadow-[0_0_10px_#00f0ff]"></div>
              )}
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-6 w-6 ${isActive('/scanner') ? 'drop-shadow-[0_0_5px_#00f0ff]' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-[10px] font-mono font-bold tracking-wider">SCAN</span>
            </Link>

            <Link 
              to="/inventory" 
              className={`flex flex-col items-center gap-1 p-2 group relative transition-colors ${isActive('/inventory') ? 'text-primary' : 'text-muted hover:text-white'}`}
            >
              {isActive('/inventory') && (
                <div className="absolute -top-[1px] left-0 right-0 h-[2px] bg-primary shadow-[0_0_10px_#00f0ff]"></div>
              )}
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-6 w-6 ${isActive('/inventory') ? 'drop-shadow-[0_0_5px_#00f0ff]' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              <span className="text-[10px] font-mono font-bold tracking-wider">STOCK</span>
            </Link>

            {/* Placeholder for Config/Future */}
            <a href="#" className="flex flex-col items-center gap-1 p-2 text-muted/50 cursor-not-allowed">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-[10px] font-mono font-bold tracking-wider">CONFIG</span>
            </a>
          </div>
        </nav>
      </div>
    </div>
  );
}
