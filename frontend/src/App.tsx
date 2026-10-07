import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { MessageSquare, FileText, Database, Shield, Moon, Sun } from 'lucide-react';
import { useState, useEffect } from 'react';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import RecordsPage from './pages/RecordsPage';
import AuditPage from './pages/AuditPage';

export default function App() {
  const [isDark, setIsDark] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (isDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [isDark]);

  const navItems = [
    { path: '/', label: 'Chat', icon: MessageSquare },
    { path: '/documents', label: 'Documents', icon: FileText },
    { path: '/records', label: 'Records', icon: Database },
  ];

  return (
    <div className="flex h-screen bg-bg text-text">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border flex flex-col hidden md:flex">
        <div className="p-4 border-b border-border">
          <h1 className="font-serif text-xl font-bold tracking-tight">University AI</h1>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <Link 
                key={item.path} 
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm transition-colors ${active ? 'bg-surface-2 text-primary font-medium' : 'text-text-muted hover:bg-surface-2 hover:text-text'}`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t border-border flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-text-subtle">
            <span className="w-2 h-2 rounded-full bg-success"></span>
            <span>API Online</span>
          </div>
          <button onClick={() => setIsDark(!isDark)} className="p-1.5 rounded-md hover:bg-surface-2 text-text-muted">
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/records" element={<RecordsPage />} />
          <Route path="/audit/:traceId" element={<AuditPage />} />
        </Routes>
      </main>
    </div>
  )
}
