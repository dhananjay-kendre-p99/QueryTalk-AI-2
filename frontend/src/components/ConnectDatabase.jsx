import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@clerk/react';
import useStore from '../store';
import axios from 'axios';

const DB_DEFAULTS = {
  postgresql: { port: '5432',  placeholder: 'production_db' },
  mysql:      { port: '3306',  placeholder: 'my_database' },
  sqlite:     { port: '',      placeholder: '/path/to/file.db' },
  snowflake:  { port: '443',   placeholder: 'MY_WAREHOUSE_DB' },
};

const DB_OPTIONS = [
  { value: 'postgresql', label: 'PostgreSQL', icon: 'storage' },
  { value: 'mysql',      label: 'MySQL',      icon: 'storage' },
  { value: 'sqlite',     label: 'SQLite',     icon: 'database' },
  { value: 'snowflake',  label: 'Snowflake',  icon: 'cloud' },
];

function Field({ label, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[11px] font-mono font-semibold text-label uppercase tracking-widest">{label}</label>
      {children}
    </div>
  );
}

export default function ConnectDatabase() {
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const { setDbStatus, setDbName, setActiveConnectionId } = useStore();

  const [dbType, setDbType] = useState('sqlite');
  const [host, setHost] = useState('');
  const [port, setPort] = useState('');
  const [dbNameLocal, setDbNameLocal] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [useSSL, setUseSSL] = useState(false);

  const [schemaPreview, setSchemaPreview] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [testSuccess, setTestSuccess] = useState(false);

  const isSQLite = dbType === 'sqlite';

  const getPayload = () => ({
    db_type: dbType,
    host: host || undefined,
    port: port ? parseInt(port) : undefined,
    db_name: dbNameLocal,
    username: username || undefined,
    password: password || undefined,
  });

  const handleTest = async () => {
    setError('');
    setSchemaPreview(null);
    setTestSuccess(false);
    setLoading(true);
    try {
      const clerkToken = await getToken();
      const res = await axios.post('/api/db/test', getPayload(), {
        headers: { Authorization: `Bearer ${clerkToken}` }
      });
      setSchemaPreview(res.data.schema);
      setTestSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Connection test failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const clerkToken = await getToken();
      const res = await axios.post('/api/db/connect', getPayload(), {
        headers: { Authorization: `Bearer ${clerkToken}` }
      });
      setDbStatus('connected');
      setDbName(dbNameLocal || 'demo.db');
      const connId = res.data.connection_id;
      if (connId) setActiveConnectionId(connId);
      navigate(connId ? `/chat/${connId}` : '/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Connection failed.');
      setLoading(false);
    }
  };

  const handleDbTypeChange = (val) => {
    setDbType(val);
    setPort(DB_DEFAULTS[val]?.port || '');
  };

  const inputClass = "glass-input w-full py-2.5 px-3.5 text-sm text-white placeholder:text-muted-foreground rounded-lg";

  return (
    <div className="min-h-screen w-screen flex items-center justify-center relative overflow-hidden bg-background">
      {/* Ambient glow */}
      <div className="absolute top-[-10%] left-[-8%] w-[500px] h-[500px] bg-primary/6 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute bottom-[-15%] right-[-10%] w-[400px] h-[400px] bg-primary/4 rounded-full blur-[140px] pointer-events-none" />

      {/* Modal backdrop */}
      <div className="fixed inset-0 bg-background/75 backdrop-blur-sm z-40 flex items-center justify-center p-4">

        {/* Modal container */}
        <div className="w-full max-w-[960px] h-[680px] bg-surface border border-outline rounded-2xl flex overflow-hidden shadow-[0_32px_80px_rgba(0,0,0,0.6)] animate-fade-up relative z-50">

          {/* ── Left: Form ─────────────────────────────────────────────── */}
          <div className="w-[54%] flex flex-col border-r border-outline">

            {/* Header */}
            <div className="px-7 py-5 border-b border-outline flex items-center justify-between shrink-0">
              <div>
                <h2 className="font-display text-lg font-bold text-white tracking-tight">Connect Database</h2>
                <p className="text-xs text-muted-foreground mt-0.5">Configure your database credentials securely.</p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/databases')}
                aria-label="Close"
                className="w-8 h-8 rounded-lg hover:bg-white/6 flex items-center justify-center text-muted-foreground hover:text-white transition-all"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            {/* Scrollable form area */}
            <div className="flex-1 overflow-y-auto px-7 py-6">
              <form className="flex flex-col gap-5" onSubmit={handleConnect}>

                {/* DB Type selector — card-style */}
                <Field label="Database Type">
                  <div className="grid grid-cols-2 gap-2">
                    {DB_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => handleDbTypeChange(opt.value)}
                        className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border text-sm font-medium transition-all duration-150 ${
                          dbType === opt.value
                            ? 'border-primary/50 bg-primary/10 text-primary'
                            : 'border-outline bg-transparent text-muted-foreground hover:border-outline-variant hover:text-white'
                        }`}
                      >
                        <span className="material-symbols-outlined text-[17px]" style={{ fontVariationSettings: dbType === opt.value ? "'FILL' 1" : "'FILL' 0" }}>{opt.icon}</span>
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </Field>

                {/* Host + Port */}
                {!isSQLite && (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <Field label="Host">
                        <input className={inputClass} placeholder="db.internal.net" type="text" value={host} onChange={e => setHost(e.target.value)} />
                      </Field>
                    </div>
                    <Field label="Port">
                      <input className={inputClass} placeholder={DB_DEFAULTS[dbType]?.port} type="number" value={port} onChange={e => setPort(e.target.value)} />
                    </Field>
                  </div>
                )}

                {/* DB Name */}
                <Field label={isSQLite ? 'File Path' : 'Database Name'}>
                  <input className={inputClass} placeholder={DB_DEFAULTS[dbType]?.placeholder || 'database_name'} type="text" value={dbNameLocal} onChange={e => setDbNameLocal(e.target.value)} />
                </Field>

                {/* Username + Password */}
                {!isSQLite && (
                  <div className="grid grid-cols-2 gap-4">
                    <Field label="Username">
                      <input className={inputClass} placeholder="db_user" type="text" value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" />
                    </Field>
                    <Field label="Password">
                      <div className="relative">
                        <input
                          className={inputClass + ' pr-10'}
                          placeholder="••••••••"
                          type={showPassword ? 'text' : 'password'}
                          value={password}
                          onChange={e => setPassword(e.target.value)}
                          autoComplete="current-password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors"
                        >
                          <span className="material-symbols-outlined text-[17px]">{showPassword ? 'visibility' : 'visibility_off'}</span>
                        </button>
                      </div>
                    </Field>
                  </div>
                )}

                {/* SSL Toggle */}
                {!isSQLite && (
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setUseSSL(!useSSL)}
                      className={`w-10 h-5 rounded-full relative transition-colors focus:outline-none ${useSSL ? 'bg-primary' : 'bg-outline-variant'}`}
                      role="switch"
                      aria-checked={useSSL}
                    >
                      <span className={`absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${useSSL ? 'translate-x-5' : 'translate-x-0'}`} />
                    </button>
                    <span className="text-sm text-muted-foreground">Require SSL / TLS</span>
                  </div>
                )}
              </form>
            </div>

            {/* Footer actions */}
            <div className="px-7 py-4 border-t border-outline flex items-center justify-between shrink-0 bg-background/40">
              <button
                type="button"
                onClick={handleTest}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-outline text-sm font-medium text-muted-foreground hover:text-white hover:border-outline-variant hover:bg-white/4 transition-all disabled:opacity-50"
              >
                <span className={`material-symbols-outlined text-[17px] ${loading ? 'animate-spin' : ''} ${testSuccess ? 'text-primary' : ''}`}>
                  {testSuccess ? 'check_circle' : 'sync'}
                </span>
                Test Connection
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => navigate('/databases')}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConnect}
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-200 disabled:opacity-50 glow-ring"
                  style={{
                    background: 'rgba(64,204,183,0.18)',
                    border: '1px solid #40CCB7',
                    color: '#40CCB7',
                    fontFamily: "'Space Grotesk', sans-serif",
                  }}
                >
                  {loading ? <span className="w-4 h-4 rounded-full border-2 border-primary/30 border-t-primary animate-spin" /> : null}
                  Connect
                  {!loading && <span className="material-symbols-outlined text-[17px]">arrow_forward</span>}
                </button>
              </div>
            </div>
          </div>

          {/* ── Right: Schema Preview ───────────────────────────────────── */}
          <div className="w-[46%] flex flex-col bg-background/60 relative overflow-hidden">
            {/* Subtle teal glow in corner */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-primary/6 rounded-full blur-[80px] pointer-events-none" />

            {/* Panel header */}
            <div className="px-7 py-5 border-b border-outline flex items-center gap-2.5 shrink-0 relative z-10">
              <span className="material-symbols-outlined text-primary text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>database</span>
              <h3 className="font-display text-sm font-semibold text-white">Schema Preview</h3>
              {testSuccess && (
                <span className="ml-auto inline-flex items-center gap-1.5 text-[11px] font-mono text-primary bg-primary/10 border border-primary/25 px-2.5 py-1 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                  Connected
                </span>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden relative z-10">
              {schemaPreview ? (
                <div className="h-full overflow-y-auto p-6">
                  <div className="bg-black/40 rounded-xl border border-outline p-5">
                    <div className="flex items-center gap-2 mb-4 pb-3 border-b border-outline/60">
                      <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
                      <span className="text-sm font-semibold text-white font-display">Connection Successful</span>
                    </div>
                    <pre className="font-mono text-[12px] text-primary/85 whitespace-pre-wrap leading-relaxed">
                      {schemaPreview}
                    </pre>
                  </div>
                </div>
              ) : error ? (
                <div className="h-full flex items-center justify-center p-6">
                  <div className="bg-error/8 border border-error/25 p-6 rounded-xl text-center w-full max-w-xs">
                    <span className="material-symbols-outlined text-error text-[36px] mb-3 block">error_outline</span>
                    <h4 className="font-display font-semibold text-white mb-2">Connection Failed</h4>
                    <p className="text-sm text-error/85 leading-relaxed">{error}</p>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center p-6 text-center gap-4">
                  {/* Terminal animation */}
                  <div className="w-full max-w-[280px] bg-black/50 rounded-xl border border-outline overflow-hidden">
                    <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-outline/60 bg-black/30">
                      <span className="w-2.5 h-2.5 rounded-full bg-error/70" />
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-400/70" />
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/70" />
                      <span className="ml-auto text-[10px] font-mono text-muted-foreground">db-tunnel</span>
                    </div>
                    <div className="p-4">
                      <pre className="font-mono text-[11px] leading-relaxed text-left">
                        <span className="text-primary/60">&gt;</span>
                        <span className="text-muted-foreground"> awaiting_handshake()</span>{'\n'}
                        <span className="text-primary/60">&gt;</span>
                        <span className="text-muted-foreground"> establishing_tunnel()</span>{'\n'}
                        <span className="text-muted-foreground/50">_ </span>
                        <span className="text-muted-foreground/50">{loading ? 'testing connection...' : 'pending credentials...'}</span>
                        {loading && <span className="inline-block ml-0.5 w-1.5 h-3.5 bg-primary animate-pulse align-middle" />}
                      </pre>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-white/70 font-medium">
                      {loading ? 'Testing connection…' : 'Awaiting Connection'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1 max-w-[220px] leading-relaxed">
                      Fill in your credentials and click <strong className="text-white/60">Test Connection</strong> to preview the schema here.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
