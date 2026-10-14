import React from 'react';

export default function ConnectDatabaseStitch() {
  return (
    <div className="font-body-sm text-body-sm antialiased overflow-hidden h-screen w-screen flex items-center justify-center relative">
{/* Background Context (Dashboard Blur) */}
<div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
<div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[120px]"></div>
<div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-secondary/5 rounded-full blur-[150px]"></div>
{/* Faux Dashboard Content Behind Blur */}
<div className="w-full h-full p-8 opacity-20 filter blur-sm">
<div className="flex gap-8 h-full">
<div className="w-64 border-r border-white/5 h-full"></div>
<div className="flex-1 flex flex-col gap-8">
<div className="h-16 border-b border-white/5 w-full"></div>
<div className="flex-1 grid grid-cols-3 gap-6">
<div className="bg-white/5 rounded-xl"></div>
<div className="col-span-2 bg-white/5 rounded-xl"></div>
<div className="col-span-3 bg-white/5 rounded-xl h-64"></div>
</div>
</div>
</div>
</div>
</div>
{/* Modal Overlay Backdrop */}
<div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 flex items-center justify-center p-4">
{/* Main Modal Container */}
<div className="w-full max-w-[1000px] h-[700px] glass-panel rounded-xl flex overflow-hidden shadow-2xl shadow-primary/5 animate-fade-in relative z-50">
{/* Left Side: Form Configuration */}
<div className="w-[55%] flex flex-col h-full border-r border-white/5 bg-surface/50">
{/* Modal Header */}
<div className="px-8 py-6 border-b border-white/5 flex items-center justify-between">
<div>
<h2 className="font-headline-md text-headline-md text-primary tracking-tight mb-1">Connect DB</h2>
<p className="font-body-sm text-body-sm text-on-surface-variant">Configure your database connection parameters securely.</p>
</div>
<button aria-label="Close Modal" className="text-on-surface-variant hover:text-white transition-colors">
<span className="material-symbols-outlined" data-weight="fill">close</span>
</button>
</div>
{/* Form Scrollable Area */}
<div className="flex-1 overflow-y-auto px-8 py-6">
<form className="flex flex-col gap-6">
{/* DB Type Selector */}
<div className="flex flex-col gap-2">
<label className="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-wider">Database Type</label>
<div className="relative">
<select className="w-full appearance-none glass-input rounded-lg px-4 py-3 font-body-sm text-body-sm text-on-surface focus:ring-0">
<option className="bg-surface-container text-on-surface" value="postgresql">PostgreSQL</option>
<option className="bg-surface-container text-on-surface" value="mysql">MySQL</option>
<option className="bg-surface-container text-on-surface" value="sqlite">SQLite</option>
<option className="bg-surface-container text-on-surface" value="snowflake">Snowflake</option>
</select>
<span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none">expand_more</span>
</div>
</div>
<div className="grid grid-cols-2 gap-6">
{/* Host */}
<div className="flex flex-col gap-2 col-span-2 sm:col-span-1">
<label className="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-wider">Host</label>
<input className="w-full glass-input rounded-lg px-4 py-3 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:ring-0" placeholder="e.g., db.internal.net" type="text"/>
</div>
{/* Port */}
<div className="flex flex-col gap-2 col-span-2 sm:col-span-1">
<label className="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-wider">Port</label>
<input className="w-full glass-input rounded-lg px-4 py-3 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:ring-0" placeholder="5432" type="number"/>
</div>
</div>
{/* Database Name */}
<div className="flex flex-col gap-2">
<label className="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-wider">Database Name</label>
<input className="w-full glass-input rounded-lg px-4 py-3 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:ring-0" placeholder="production_db" type="text"/>
</div>
<div className="grid grid-cols-2 gap-6">
{/* Username */}
<div className="flex flex-col gap-2 col-span-2 sm:col-span-1">
<label className="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-wider">Username</label>
<input className="w-full glass-input rounded-lg px-4 py-3 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:ring-0" placeholder="admin_user" type="text"/>
</div>
{/* Password */}
<div className="flex flex-col gap-2 col-span-2 sm:col-span-1">
<label className="font-label-mono text-label-mono text-on-surface-variant uppercase tracking-wider">Password</label>
<div className="relative">
<input className="w-full glass-input rounded-lg px-4 py-3 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:ring-0" placeholder="••••••••" type="password"/>
<button className="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-white transition-colors" type="button">
<span className="material-symbols-outlined text-[18px]">visibility_off</span>
</button>
</div>
</div>
</div>
{/* SSL Toggle */}
<div className="flex items-center gap-3 mt-2">
<button className="w-10 h-5 bg-primary/20 rounded-full relative transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50" type="button">
<span className="absolute left-1 top-1 w-3 h-3 bg-primary rounded-full transition-transform translate-x-5"></span>
</button>
<span className="font-body-sm text-body-sm text-on-surface-variant">Require SSL/TLS connection</span>
</div>
</form>
</div>
{/* Action Footer */}
<div className="px-8 py-5 border-t border-white/5 flex items-center justify-between bg-surface-container-low/30">
<button className="px-5 py-2.5 rounded-lg border border-white/10 text-on-surface font-medium hover:bg-white/5 transition-all flex items-center gap-2 group">
<span className="material-symbols-outlined text-[18px] text-outline group-hover:text-primary transition-colors">sync</span>
                        Test Connection
                    </button>
<div className="flex gap-3">
<button className="px-5 py-2.5 rounded-lg text-on-surface-variant font-medium hover:text-white transition-colors">Cancel</button>
<button className="px-6 py-2.5 bg-primary/60 hover:bg-primary/80 border border-primary text-white rounded-lg font-medium shadow-lg shadow-primary/20 transition-all flex items-center gap-2">
                            Connect
                            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
</button>
</div>
</div>
</div>
{/* Right Side: Schema Preview Panel */}
<div className="w-[45%] flex flex-col h-full bg-surface-container-lowest/80 relative">
{/* Subtle Gradient Glow Top Right */}
<div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-[80px] pointer-events-none"></div>
<div className="px-8 py-6 border-b border-white/5 flex items-center gap-3">
<span className="material-symbols-outlined text-secondary">database</span>
<h3 className="font-headline-md text-body-lg font-medium text-on-surface">Schema Preview</h3>
</div>
{/* Preview Content State (Empty/Awaiting Connection) */}
<div className="flex-1 flex flex-col items-center justify-center p-8 text-center relative z-10">
<div className="w-24 h-24 rounded-full border border-white/5 bg-white/5 flex items-center justify-center mb-6 relative">
<div className="absolute inset-0 rounded-full border border-primary/20 animate-[spin_4s_linear_infinite]"></div>
<span className="material-symbols-outlined text-[40px] text-outline-variant">schema</span>
</div>
<h4 className="font-body-lg text-body-lg text-on-surface mb-2">Awaiting Connection</h4>
<p className="font-body-sm text-body-sm text-on-surface-variant max-w-[250px]">
                        Enter your credentials and click "Test Connection" to preview the database schema, tables, and views here.
                    </p>
{/* Mock Code Snippet to simulate technical environment */}
<div className="mt-8 p-4 rounded-lg bg-black/40 border border-white/5 w-full text-left overflow-hidden">
<div className="flex items-center gap-2 mb-3">
<div className="w-2 h-2 rounded-full bg-error"></div>
<div className="w-2 h-2 rounded-full bg-tertiary-container"></div>
<div className="w-2 h-2 rounded-full bg-secondary"></div>
</div>
<pre className="font-label-mono text-label-mono text-outline-variant">&gt; awaiting_handshake()
&gt; establishing_tunnel()
_ pending credentials...</pre>
</div>
</div>
</div>
</div>
</div>
    </div>
  );
}
