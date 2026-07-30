import React, { useState, useEffect } from 'react';
import CapturePage from './pages/CapturePage.jsx';
import AuthPage from './pages/AuthPage.jsx';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("React ErrorBoundary caught error:", error, errorInfo);
  }

  handleReset = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_profile');
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ backgroundColor: '#0b0f17', color: '#fff', height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.5rem', color: '#f87171', marginBottom: '12px' }}>⚠️ Application Session Reset Required</h2>
          <p style={{ color: '#9ca3af', marginBottom: '20px', maxWidth: '500px' }}>
            A session state mismatch occurred from a previous login attempt. Click below to reset your session and return to the login screen.
          </p>
          <button
            onClick={this.handleReset}
            style={{ padding: '12px 24px', backgroundColor: '#10b981', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '1rem', fontWeight: 600, cursor: 'pointer' }}
          >
            🔄 Reset Session & Return to Login
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user_profile');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        if (parsed && typeof parsed === 'object' && parsed.id) {
          setCurrentUser(parsed);
        } else {
          localStorage.removeItem('user_profile');
        }
      } catch (e) {
        localStorage.removeItem('user_profile');
      }
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_profile');
    setCurrentUser(null);
  };

  if (loading) {
    return (
      <div style={{ backgroundColor: '#0b0f17', color: '#fff', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        Loading Healthcare System...
      </div>
    );
  }

  if (!currentUser) {
    return (
      <ErrorBoundary>
        <AuthPage onLoginSuccess={(user) => setCurrentUser(user)} />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <CapturePage currentUser={currentUser} onLogout={handleLogout} />
    </ErrorBoundary>
  );
}

export default App;
