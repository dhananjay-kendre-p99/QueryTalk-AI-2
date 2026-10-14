import React from 'react'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/react'
import './index.css'
import App from './App.jsx'

// Get the key from Vite env
const activeKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

// Check if the key is valid (not empty and not a generic placeholder)
const isValidKey = activeKey && 
  activeKey.trim() !== '' && 
  !activeKey.includes('placeholder') && 
  !activeKey.includes('your_clerk_publishable_key');

function ClerkSetupGuide() {
  return (
    <div className="min-h-screen w-screen bg-[#020617] text-[#dce1fb] font-display flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-[-100px] left-[10%] w-[500px] h-[500px] bg-[#adc6ff] rounded-full mix-blend-screen filter blur-[150px] opacity-10 pointer-events-none" />
      <div className="absolute bottom-[-100px] right-[10%] w-[400px] h-[400px] bg-[#df7412] rounded-full mix-blend-screen filter blur-[150px] opacity-10 pointer-events-none" />

      {/* Main card */}
      <div className="relative w-full max-w-2xl bg-[#0c1324]/60 backdrop-blur-2xl border border-white/10 rounded-[1rem] p-8 shadow-2xl flex flex-col gap-6">
        
        {/* Title / Icon */}
        <div className="flex items-center gap-4 border-b border-white/5 pb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-[#adc6ff] to-[#4d8eff] flex items-center justify-center shadow-lg shadow-[#adc6ff]/10">
            <span className="material-symbols-outlined text-[#002e6a] text-2xl font-bold">vpn_key</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#adc6ff] tracking-tight">Clerk Authentication Setup Required</h1>
            <p className="text-sm text-[#8c909f]">Configure your environment variables to launch the dashboard.</p>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-[#191f31]/40 rounded-xl p-4 border border-white/5 text-sm text-[#c2c6d6] leading-relaxed">
          <p>
            QueryTalk AI uses <strong>Clerk</strong> for secure user authentication and database role separation.
            To view the frontend, you need to provide your Clerk <strong>Publishable Key</strong>.
          </p>
        </div>

        {/* Steps */}
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-[#adc6ff] flex items-center gap-2">
            <span className="material-symbols-outlined text-[20px]">list</span> Setup Steps
          </h2>
          
          <div className="flex flex-col gap-3 text-sm text-[#c2c6d6]">
            <div className="flex gap-3">
              <span className="w-6 h-6 rounded-full bg-[#adc6ff]/10 border border-[#adc6ff]/20 text-[#adc6ff] flex items-center justify-center font-bold text-xs shrink-0">1</span>
              <div>
                <p className="font-semibold text-[#dce1fb]">Get your keys from Clerk</p>
                <p className="text-xs text-[#8c909f] mt-0.5">
                  Sign up for free at <a href="https://clerk.com" target="_blank" rel="noopener noreferrer" className="text-[#adc6ff] hover:underline">clerk.com</a>, create an application, and go to the <strong>API Keys</strong> tab.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <span className="w-6 h-6 rounded-full bg-[#adc6ff]/10 border border-[#adc6ff]/20 text-[#adc6ff] flex items-center justify-center font-bold text-xs shrink-0">2</span>
              <div className="w-full">
                <p className="font-semibold text-[#dce1fb]">Configure Environment Variables</p>
                <p className="text-xs text-[#8c909f] mt-0.5">Create a <code>.env</code> file in both your frontend and backend directories:</p>
                
                {/* Env code displays */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
                  <div className="bg-[#070d1f] p-3 rounded-lg border border-white/5">
                    <p className="text-[10px] font-semibold text-[#adc6ff] mb-1 font-label-mono">FRONTEND /frontend/.env</p>
                    <pre className="text-xs font-mono text-[#dce1fb] overflow-x-auto select-all">
                      VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
                    </pre>
                  </div>
                  <div className="bg-[#070d1f] p-3 rounded-lg border border-white/5">
                    <p className="text-[10px] font-semibold text-[#df7412] mb-1 font-label-mono">BACKEND /backend/.env</p>
                    <pre className="text-xs font-mono text-[#dce1fb] overflow-x-auto select-all">
                      CLERK_PUBLISHABLE_KEY=pk_test_...
                    </pre>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <span className="w-6 h-6 rounded-full bg-[#adc6ff]/10 border border-[#adc6ff]/20 text-[#adc6ff] flex items-center justify-center font-bold text-xs shrink-0">3</span>
              <div>
                <p className="font-semibold text-[#dce1fb]">Restart Servers</p>
                <p className="text-xs text-[#8c909f] mt-0.5">Stop your development servers and restart them so they load the new env files.</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

if (!isValidKey) {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <ClerkSetupGuide />
    </StrictMode>,
  )
} else {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <ClerkProvider publishableKey={activeKey}>
        <App />
      </ClerkProvider>
    </StrictMode>,
  )
}
