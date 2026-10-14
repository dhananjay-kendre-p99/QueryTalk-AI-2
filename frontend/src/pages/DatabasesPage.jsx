import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useClerk } from '@clerk/react';
import axios from 'axios';
import useStore from '../store';

const DB_TYPE_META = {
  postgresql: { label: 'PostgreSQL', color: 'text-sky-400',    bg: 'bg-sky-400/8',    border: 'border-sky-400/20',    icon: 'storage' },
  mysql:      { label: 'MySQL',      color: 'text-orange-400', bg: 'bg-orange-400/8', border: 'border-orange-400/20', icon: 'storage' },
  sqlite:     { label: 'SQLite',     color: 'text-emerald-400',bg: 'bg-emerald-400/8',border: 'border-emerald-400/20',icon: 'database' },
  snowflake:  { label: 'Snowflake',  color: 'text-cyan-400',   bg: 'bg-cyan-400/8',   border: 'border-cyan-400/20',   icon: 'cloud' },
};

function DbTypeBadge({ type }) {
  const m = DB_TYPE_META[type?.toLowerCase()] ?? DB_TYPE_META.sqlite;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold uppercase tracking-wider border ${m.bg} ${m.border} ${m.color}`}>
      <span className="material-symbols-outlined text-[13px]" style={{ fontVariationSettings: "'FILL' 1" }}>{m.icon}</span>
      {m.label}
    </span>
  );
}

function ConnectionCard({ conn, onConnect, onDelete, connecting, deleteConfirm }) {
  const isConnecting = connecting === conn.id;
  const isPendingDelete = deleteConfirm === conn.id;
  const updatedAt = new Date(conn.updated_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  return (
    <div className={`group relative bg-surface border rounded-2xl p-6 flex flex-col gap-4 transition-all duration-200 ${isPendingDelete ? 'border-error/40 bg-error/5' : 'border-outline hover:border-primary/30 hover:shadow-[0_0_24px_rgba(64,204,183,0.1)]'}`}>

      {/* Delete pending indicator */}
      {isPendingDelete && (
        <div className="absolute inset-x-0 top-0 h-0.5 bg-error rounded-t-2xl" />
      )}

      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0 transition-colors group-hover:bg-primary/15">
          <span className="material-symbols-outlined text-primary text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>database</span>
        </div>
        <button
          onClick={() => onDelete(conn.id)}
          aria-label="Delete connection"
          title={isPendingDelete ? 'Click again to confirm' : 'Delete connection'}
          className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${isPendingDelete ? 'opacity-100 bg-error/15 text-error' : 'opacity-0 group-hover:opacity-100 hover:bg-error/10 text-muted-foreground hover:text-error'}`}
        >
          <span className="material-symbols-outlined text-[17px]">{isPendingDelete ? 'warning' : 'delete'}</span>
        </button>
      </div>

      {/* Name + type */}
      <div className="flex flex-col gap-2 flex-1">
        <h3 className="font-display font-semibold text-white text-base truncate leading-tight">{conn.name}</h3>
        <DbTypeBadge type={conn.db_type} />
      </div>

      {/* Meta */}
      <div className="flex flex-col gap-1.5">
        {conn.host_hint && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="material-symbols-outlined text-[14px]">dns</span>
            <span className="font-mono text-[12px] truncate">{conn.host_hint}</span>
          </div>
        )}
        {conn.db_name_hint && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="material-symbols-outlined text-[14px]">table_chart</span>
            <span className="font-mono text-[12px] truncate">{conn.db_name_hint}</span>
          </div>
        )}
        <div className="flex items-center gap-2 text-muted-foreground/60">
          <span className="material-symbols-outlined text-[13px]">schedule</span>
          <span className="text-[11px]">Last used {updatedAt}</span>
        </div>
      </div>

      {/* Connect button */}
      <button
        onClick={() => onConnect(conn)}
        disabled={isConnecting || isPendingDelete}
        className="mt-1 w-full py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
        style={{
          background: 'rgba(64, 204, 183, 0.15)',
          border: '1px solid rgba(64, 204, 183, 0.5)',
          color: '#40CCB7',
          fontFamily: "'Space Grotesk', sans-serif",
        }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(64,204,183,0.25)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(64,204,183,0.18)'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(64,204,183,0.15)'; e.currentTarget.style.boxShadow = 'none'; }}
      >
        {isConnecting ? (
          <>
            <span className="w-4 h-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            Connecting…
          </>
        ) : (
          <>
            <span className="material-symbols-outlined text-[18px]">power</span>
            Connect
          </>
        )}
      </button>
    </div>
  );
}

function EmptyState({ onAdd }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[56vh] text-center px-4 animate-fade-up">
      <div className="relative w-28 h-28 mb-8">
        <div className="absolute inset-0 rounded-full border border-primary/10 animate-ping" style={{ animationDuration: '3s' }} />
        <div className="absolute inset-3 rounded-full border border-primary/15" />
        <div className="w-full h-full rounded-full bg-primary/6 border border-primary/12 flex items-center justify-center">
          <span className="material-symbols-outlined text-primary/70 text-[48px]" style={{ fontVariationSettings: "'FILL' 1" }}>database</span>
        </div>
      </div>
      <h2 className="font-display text-2xl font-bold text-white mb-2">No databases connected</h2>
      <p className="text-muted-foreground max-w-xs mb-8 leading-relaxed">
        Connect your first database to start querying with natural language.
      </p>
      <button
        onClick={onAdd}
        id="add-first-database-btn"
        className="flex items-center gap-2 px-7 py-3 rounded-xl text-sm font-semibold transition-all duration-200"
        style={{
          background: 'rgba(64,204,183,0.18)',
          border: '1px solid #40CCB7',
          color: '#40CCB7',
          fontFamily: "'Space Grotesk', sans-serif",
        }}
      >
        <span className="material-symbols-outlined text-[18px]">add</span>
        Connect your first database
      </button>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-surface border border-outline rounded-2xl p-6 flex flex-col gap-4 animate-pulse">
      <div className="w-10 h-10 rounded-xl bg-white/5" />
      <div className="flex flex-col gap-2">
        <div className="h-4 bg-white/5 rounded-lg w-3/5" />
        <div className="h-6 bg-white/5 rounded-full w-24" />
      </div>
      <div className="flex flex-col gap-2">
        <div className="h-3.5 bg-white/5 rounded w-2/3" />
        <div className="h-3 bg-white/5 rounded w-1/2" />
      </div>
      <div className="h-10 bg-white/5 rounded-xl mt-1" />
    </div>
  );
}

export default function DatabasesPage() {
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const { setDbStatus, setDbName, setActiveConnectionId } = useStore();

  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(null);
  const [error, setError] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const fetchConnections = async () => {
    setLoading(true);
    setError('');
    try {
      const token = await getToken();
      const res = await axios.get('/api/db/saved', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setConnections(res.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setConnections([]);
      } else {
        setError('Failed to load your databases. Please refresh.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchConnections(); }, []);

  const handleConnect = async (conn) => {
    setConnecting(conn.id);
    try {
      const token = await getToken();
      await axios.post(`/api/db/reconnect/${conn.id}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDbStatus('connected');
      setDbName(conn.name);
      setActiveConnectionId(conn.id);
      navigate(`/chat/${conn.id}`);
    } catch (err) {
      setError(`Failed to connect to "${conn.name}": ${err.response?.data?.detail || err.message}`);
      setConnecting(null);
    }
  };

  const handleDelete = async (id) => {
    if (deleteConfirm !== id) {
      setDeleteConfirm(id);
      setTimeout(() => setDeleteConfirm(c => c === id ? null : c), 3000);
      return;
    }
    try {
      const token = await getToken();
      await axios.delete(`/api/db/saved/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setConnections(prev => prev.filter(c => c.id !== id));
      setDeleteConfirm(null);
    } catch (err) {
      setError('Failed to delete connection.');
    }
  };

  const handleLogout = async () => {
    await signOut();
    navigate('/sign-in');
  };

  return (
    <div className="min-h-screen bg-background antialiased">
      {/* Subtle ambient teal glow top-left */}
      <div className="fixed top-[-120px] left-[5%] w-[520px] h-[520px] bg-primary/6 rounded-full blur-[180px] pointer-events-none" />

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-surface/60 backdrop-blur-xl border-b border-outline">
        <div className="max-w-6xl mx-auto px-6 md:px-10 h-16 flex items-center justify-between gap-4">

          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/15 border border-primary/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
            </div>
            <div className="leading-tight">
              <p className="font-display font-bold text-white text-[15px] leading-none">QueryTalk AI</p>
              <p className="text-[10px] font-mono text-muted-foreground tracking-widest uppercase leading-none mt-0.5">Enterprise Tier</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              id="add-database-btn"
              onClick={() => navigate('/connect')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 glow-ring"
              style={{
                background: 'rgba(64,204,183,0.15)',
                border: '1px solid #40CCB7',
                color: '#40CCB7',
                fontFamily: "'Space Grotesk', sans-serif",
              }}
            >
              <span className="material-symbols-outlined text-[17px]">add</span>
              <span className="hidden sm:inline">Add Database</span>
            </button>
            <button
              onClick={handleLogout}
              className="w-9 h-9 rounded-lg border border-outline hover:border-outline-variant hover:bg-white/4 flex items-center justify-center text-muted-foreground hover:text-error transition-all"
              aria-label="Sign out"
              title="Sign out"
            >
              <span className="material-symbols-outlined text-[18px]">logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <main className="max-w-6xl mx-auto px-6 md:px-10 py-10">

        {/* Page title */}
        <div className="mb-8">
          <h2 className="font-display text-2xl font-bold text-white tracking-tight">My Databases</h2>
          <p className="text-muted-foreground mt-1 text-sm">Select a connection to start querying with AI.</p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-6 flex items-center gap-3 px-4 py-3 rounded-xl bg-error/8 border border-error/25 text-error animate-fade-up">
            <span className="material-symbols-outlined text-[18px] shrink-0">error</span>
            <p className="text-sm flex-1">{error}</p>
            <button onClick={() => setError('')} className="hover:opacity-70 transition-opacity">
              <span className="material-symbols-outlined text-[16px]">close</span>
            </button>
          </div>
        )}

        {/* Delete confirmation */}
        {deleteConfirm && (
          <div className="mb-6 flex items-center gap-3 px-4 py-3 rounded-xl bg-amber-400/8 border border-amber-400/25 text-amber-400 animate-fade-up">
            <span className="material-symbols-outlined text-[18px] shrink-0">warning</span>
            <p className="text-sm flex-1 text-white/85">Click delete again to <strong className="text-white">confirm removal</strong> of this connection.</p>
            <button onClick={() => setDeleteConfirm(null)} className="text-muted-foreground hover:text-white text-xs underline underline-offset-2 transition-colors">
              Cancel
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
          </div>
        )}

        {/* Empty state */}
        {!loading && connections.length === 0 && (
          <EmptyState onAdd={() => navigate('/connect')} />
        )}

        {/* Connection cards */}
        {!loading && connections.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {connections.map(conn => (
              <ConnectionCard
                key={conn.id}
                conn={conn}
                onConnect={handleConnect}
                onDelete={handleDelete}
                connecting={connecting}
                deleteConfirm={deleteConfirm}
              />
            ))}

            {/* Add new card */}
            <button
              onClick={() => navigate('/connect')}
              id="add-another-database-btn"
              className="group border border-dashed border-outline hover:border-primary/40 rounded-2xl p-6 flex flex-col items-center justify-center gap-3 text-muted-foreground hover:text-primary transition-all duration-200 min-h-[220px] cursor-pointer"
            >
              <div className="w-10 h-10 rounded-xl border border-dashed border-current flex items-center justify-center group-hover:bg-primary/8 transition-colors">
                <span className="material-symbols-outlined text-[22px]">add</span>
              </div>
              <span className="text-sm font-semibold font-display">Add Database</span>
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
