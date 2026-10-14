import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore from '../store';
import axios from 'axios';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const setToken = useStore((state) => state.setToken);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await axios.post('/api/auth/login', {
        username: email,
        password: password
      });
      setToken(res.data.access_token);
      navigate('/connect');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen flex items-center justify-center relative overflow-hidden bg-background">
      {/* Ambient glow orbs */}
      <div className="absolute top-[-15%] left-[-10%] w-[500px] h-[500px] rounded-full bg-primary/8 blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-15%] right-[-10%] w-[450px] h-[450px] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />

      {/* Login card */}
      <main className="relative z-10 w-full max-w-[420px] mx-4 md:mx-auto animate-fade-up">
        <div className="bg-surface border border-outline rounded-2xl p-8 shadow-[0_24px_64px_rgba(0,0,0,0.5)]">

          {/* Brand */}
          <div className="flex flex-col items-center mb-8 text-center">
            <div className="w-12 h-12 rounded-xl bg-primary/15 border border-primary/30 flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-primary text-[24px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
            </div>
            <h1 className="font-display text-2xl font-bold text-white tracking-tight">QueryTalk AI</h1>
            <p className="text-sm text-muted-foreground mt-1.5">Sign in to your command center</p>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2.5 bg-error/8 border border-error/25 text-error px-4 py-3 rounded-xl text-sm mb-5">
              <span className="material-symbols-outlined text-[18px] shrink-0">error</span>
              {error}
            </div>
          )}

          {/* Form */}
          <form className="flex flex-col gap-4" onSubmit={handleLogin}>

            {/* Email */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-label uppercase tracking-widest font-mono" htmlFor="login-email">
                Email Address
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground text-[18px] pointer-events-none" style={{ fontVariationSettings: "'FILL' 1" }}>mail</span>
                <input
                  id="login-email"
                  className="glass-input w-full py-3 pl-10 pr-4 text-sm text-white"
                  placeholder="engineer@querytalk.ai"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold text-label uppercase tracking-widest font-mono" htmlFor="login-password">
                  Password
                </label>
                <a className="text-xs text-primary hover:text-primary/80 transition-colors" href="#">Forgot password?</a>
              </div>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground text-[18px] pointer-events-none" style={{ fontVariationSettings: "'FILL' 1" }}>lock</span>
                <input
                  id="login-password"
                  className="glass-input w-full py-3 pl-10 pr-11 text-sm text-white"
                  placeholder="••••••••"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors"
                >
                  <span className="material-symbols-outlined text-[18px]">{showPassword ? 'visibility' : 'visibility_off'}</span>
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 rounded-xl flex items-center justify-center gap-2 text-sm font-semibold transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed glow-ring"
              style={{
                background: 'rgba(64, 204, 183, 0.18)',
                border: '1px solid #40CCB7',
                color: '#40CCB7',
                fontFamily: "'Space Grotesk', sans-serif",
              }}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-primary/30 border-t-primary animate-spin" />
                  Signing in…
                </>
              ) : (
                <>
                  Sign In
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-outline" />
            <span className="text-[11px] font-mono text-muted-foreground uppercase tracking-widest px-1">or continue with</span>
            <div className="flex-1 h-px bg-outline" />
          </div>

          {/* Google */}
          <button
            type="button"
            className="w-full py-3 rounded-xl border border-outline bg-transparent text-white/80 hover:bg-white/4 hover:border-outline-variant text-sm font-medium flex items-center justify-center gap-3 transition-all duration-200"
          >
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>

          {/* Footer */}
          <p className="text-center text-sm text-muted-foreground mt-6">
            Don't have an account?{' '}
            <a className="text-primary hover:text-primary/80 transition-colors font-medium" href="#">Request Access</a>
          </p>
        </div>

        {/* Trust signal */}
        <p className="text-center text-xs text-muted-foreground/50 mt-5 font-mono">
          End-to-end encrypted · SOC 2 compliant
        </p>
      </main>
    </div>
  );
}
