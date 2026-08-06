import { useEffect, useState } from 'react';
import Login from './components/Login';
import Header from './components/Header';
import EditorView from './components/EditorView';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [username, setUsername] = useState(() => localStorage.getItem('username') || '');
  const [checking, setChecking] = useState(true);

  // Validate stored token on mount
  useEffect(() => {
    const validate = async () => {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        setChecking(false);
        return;
      }
      try {
        const res = await fetch(`${API_URL}/api/me`, {
          headers: { Authorization: `Bearer ${storedToken}` },
        });
        if (res.ok) {
          const data = await res.json();
          setUsername(data.username);
          localStorage.setItem('username', data.username);
        } else {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          setToken(null);
          setUsername('');
        }
      } catch {
        // Keep token if network error; user can retry
      } finally {
        setChecking(false);
      }
    };
    validate();
  }, []);

  const handleLogin = (newToken, newUsername) => {
    setToken(newToken);
    setUsername(newUsername);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setToken(null);
    setUsername('');
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-sm mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      <Header username={username} onLogout={handleLogout} />
      <EditorView token={token} />
    </div>
  );
}
