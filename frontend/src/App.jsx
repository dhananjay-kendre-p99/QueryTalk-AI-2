import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@clerk/react';
import SignInPage from './pages/SignInPage';
import SignUpPage from './pages/SignUpPage';
import DatabasesPage from './pages/DatabasesPage';
import ChatDashboard from './components/ChatDashboard';
import ConnectDatabase from './components/ConnectDatabase';
import LandingPage from './pages/LandingPage';

/** Full-screen loading spinner shown while Clerk resolves the auth state */
function AuthLoader() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
        <span className="font-mono text-xs text-muted-foreground uppercase tracking-widest">
          Loading…
        </span>
      </div>
    </div>
  );
}

/**
 * Public home route:
 *  - Unauthenticated → LandingPage
 *  - Authenticated   → /databases
 */
function HomeRoute() {
  const { isSignedIn, isLoaded } = useAuth();
  if (!isLoaded) return <AuthLoader />;
  return isSignedIn ? <Navigate to="/databases" replace /> : <LandingPage />;
}

/** Wraps a route so only authenticated users can access it */
function ProtectedRoute({ children }) {
  const { isSignedIn, isLoaded } = useAuth();
  if (!isLoaded) return <AuthLoader />;
  return isSignedIn ? children : <Navigate to="/sign-in" replace />;
}

/** Redirects already-authenticated users away from auth pages */
function AuthRoute({ children }) {
  const { isSignedIn, isLoaded } = useAuth();
  if (!isLoaded) return <AuthLoader />;
  return !isSignedIn ? children : <Navigate to="/databases" replace />;
}

function App() {
  return (
    <Router>
      <Routes>
        {/* Public landing — shows LandingPage to guests, redirects signed-in users */}
        <Route path="/" element={<HomeRoute />} />

        {/* Auth routes — redirect to /databases if already signed in */}
        <Route path="/sign-in/*" element={<AuthRoute><SignInPage /></AuthRoute>} />
        <Route path="/sign-up/*" element={<AuthRoute><SignUpPage /></AuthRoute>} />

        {/* Legacy /login path */}
        <Route path="/login" element={<Navigate to="/sign-in" replace />} />

        {/* Protected app routes */}
        <Route path="/databases" element={<ProtectedRoute><DatabasesPage /></ProtectedRoute>} />
        <Route path="/chat/:connectionId" element={<ProtectedRoute><ChatDashboard /></ProtectedRoute>} />
        <Route path="/connect" element={<ProtectedRoute><ConnectDatabase /></ProtectedRoute>} />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
