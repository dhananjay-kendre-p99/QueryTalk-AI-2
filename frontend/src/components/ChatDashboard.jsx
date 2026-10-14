import { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth, useClerk } from '@clerk/react';
import useStore from '../store';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import AnalyticsDashboard from './AnalyticsDashboard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatDashboard() {
  const navigate = useNavigate();
  const { connectionId } = useParams();
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  const { chats, activeChatId, addMessage, createNewChat, setActiveChatId, dbStatus, dbName, apiKey, setApiKey, setDbStatus, setDbName, setActiveConnectionId, activeConnectionId } = useStore();
  const [schemaData, setSchemaData] = useState('');
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [tablesData, setTablesData] = useState([]);
  const [loadingTables, setLoadingTables] = useState(false);
  const [tablesError, setTablesError] = useState('');
  const [expandedTable, setExpandedTable] = useState(null);
  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];
  const chatHistory = activeChat ? activeChat.messages : [];
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-reconnect when arriving via URL (e.g. page refresh)
  useEffect(() => {
    if (!connectionId) return;
    if (activeConnectionId === connectionId && dbStatus === 'connected') return;
    const reconnect = async () => {
      setReconnecting(true);
      try {
        const token = await getToken();
        const res = await axios.post(`/api/db/reconnect/${connectionId}`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setDbStatus('connected');
        setDbName(res.data.name || connectionId);
        setActiveConnectionId(connectionId);
      } catch (err) {
        // Reconnect failed — redirect back to databases page
        navigate('/databases');
      } finally {
        setReconnecting(false);
      }
    };
    reconnect();
  }, [connectionId]);

  useEffect(() => {
    // bypass dbStatus check for now so UI can be seen
    // if (dbStatus === 'disconnected') {
    //   navigate('/connect');
    // }
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [dbStatus, chatHistory, navigate]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    addMessage({ role: 'user', content: userMsg });
    setLoading(true);

    try {
      const clerkToken = await getToken();
      const res = await axios.post(
        '/api/chat/',
        { message: userMsg },
        { headers: { Authorization: `Bearer ${clerkToken}`, 'X-API-Key': apiKey || '' } }
      );
      addMessage({
        role: 'assistant',
        content: res.data.reply,
        sql: res.data.sql,
        data: res.data.data
      });
    } catch (err) {
      console.error(err);
      addMessage({ role: 'assistant', content: 'Error communicating with the server.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'databases' && dbStatus === 'connected') {
      const fetchSchema = async () => {
        setLoadingSchema(true);
        try {
          const clerkToken = await getToken();
          const res = await axios.get('/api/db/schema', { headers: { Authorization: `Bearer ${clerkToken}` }});
          setSchemaData(res.data.schema);
        } catch(e) {
          console.error(e);
          setSchemaData('Failed to load schema.');
        } finally {
          setLoadingSchema(false);
        }
      };
      fetchSchema();
    }
  }, [activeTab, dbStatus, getToken]);

  useEffect(() => {
    if (activeTab === 'tables' && connectionId) {
      const fetchTables = async () => {
        setLoadingTables(true);
        setTablesError('');
        try {
          const clerkToken = await getToken();
          const res = await axios.get(`/api/db/connections/${connectionId}/schema`, {
            headers: { Authorization: `Bearer ${clerkToken}` },
          });
          setTablesData(res.data.tables || []);
          if (res.data.tables && res.data.tables.length > 0) {
            setExpandedTable(res.data.tables[0].full_name);
          }
        } catch (e) {
          console.error(e);
          setTablesError('Failed to load table structure. Make sure you are connected to a database.');
        } finally {
          setLoadingTables(false);
        }
      };
      fetchTables();
    }
  }, [activeTab, connectionId, getToken]);

  const handleLogout = async () => {
    await signOut();
    navigate('/sign-in');
  };

  const renderChart = (data) => {
    if (!data || data.length === 0) return null;
    
    const keys = Object.keys(data[0]);
    const stringKey = keys.find(k => typeof data[0][k] === 'string') || keys[0];
    const numberKey = keys.find(k => typeof data[0][k] === 'number');

    if (!numberKey) return null;

    return (
      <div className="h-64 mt-4 bg-surface-container-low/60 backdrop-blur-md rounded-xl border border-white/5 overflow-hidden p-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey={stringKey} stroke="#a0b4c4" />
            <YAxis stroke="#a0b4c4" />
            <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{backgroundColor: '#1a2438', border: 'none', borderRadius: '8px', color: '#fff'}} />
            <Bar dataKey={numberKey} fill="#7dd3fc" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };
  
  const renderTable = (data) => {
    return <PreviewTable data={data} />;
  };

  return (
    <div className="antialiased fixed inset-0 flex flex-col overflow-hidden bg-background">
      {/* Reconnecting overlay */}
      {reconnecting && (
        <div className="absolute inset-0 z-[9999] bg-background/92 backdrop-blur-sm flex flex-col items-center justify-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest">Reconnecting to database…</p>
        </div>
      )}

      {/* ── Top Navbar ─────────────────────────────────────────────────── */}
      <header className="w-full bg-surface/70 backdrop-blur-xl border-b border-outline flex justify-between items-center h-14 px-4 md:px-6 z-50 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden w-9 h-9 flex items-center justify-center text-muted-foreground hover:text-primary hover:bg-white/5 rounded-lg transition-all"
          >
            <span className="material-symbols-outlined text-[22px]">{sidebarOpen ? 'close' : 'menu'}</span>
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-primary/15 border border-primary/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
            </div>
            <div className="leading-tight">
              <h1 className="font-display font-bold text-white text-[14px] leading-none">QueryTalk AI</h1>
              <p className="hidden md:block text-[10px] font-mono text-muted-foreground tracking-widest uppercase leading-none mt-0.5">Enterprise Tier</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-3">
          {/* DB status badge */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/8 border border-primary/20">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="font-mono text-[11px] text-primary truncate max-w-[160px]">{dbName || 'demo.db'}</span>
          </div>

          <div className="hidden md:block w-px h-5 bg-outline mx-1" />

          <button
            onClick={() => setActiveTab('notifications')}
            className={`hidden sm:flex w-8 h-8 rounded-lg items-center justify-center transition-all hover:bg-white/5 ${activeTab === 'notifications' ? 'text-primary' : 'text-muted-foreground'}`}
          >
            <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: activeTab === 'notifications' ? "'FILL' 1" : "'FILL' 0" }}>notifications</span>
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`hidden sm:flex w-8 h-8 rounded-lg items-center justify-center transition-all hover:bg-white/5 ${activeTab === 'security' ? 'text-primary' : 'text-muted-foreground'}`}
          >
            <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: activeTab === 'security' ? "'FILL' 1" : "'FILL' 0" }}>shield</span>
          </button>

          <button
            onClick={() => navigate('/databases')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all glow-ring"
            style={{ background: 'rgba(64,204,183,0.12)', border: '1px solid rgba(64,204,183,0.4)', color: '#40CCB7', fontFamily: "'Space Grotesk', sans-serif" }}
          >
            <span className="material-symbols-outlined text-[15px]">swap_horiz</span>
            <span className="hidden sm:inline">Switch DB</span>
          </button>

          <div className="w-8 h-8 rounded-full overflow-hidden border-2 border-outline shrink-0">
            <img alt="User" className="w-full h-full object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAlUlP37Kr7hG9AMroagV09jBtw_oQkciSuV9RfKSHQdcqn3CSaDNtcf5AjH2kZcjyoniZavtoNE1XpLBWV4HYDBwDB7Vlg6jiQ-OYU8WmPeTVAy25L54yk1c0SXK_HhbVxdlOH2dogkttXeBlW3Xj-0j3zAHT9pUqNsNV3uoyfKT_b9-CLpNQJ_J-fSjfua2RdUyZsbmsP3xYNLX231W2T5Za78gG9zVHwFssV4lqpB5P52JVqxIToxvJagzvZNgsP8GNGuYGQOUR_" />
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden relative">
        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-30 md:hidden" onClick={() => setSidebarOpen(false)}></div>
        )}
        
        {/* ── Sidebar ──────────────────────────────────────────────────── */}
        <aside className={`absolute md:static top-0 left-0 h-full w-[256px] bg-surface border-r border-outline backdrop-blur-xl shadow-[4px_0_32px_rgba(0,0,0,0.3)] flex flex-col p-4 z-40 transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>

          {/* New Chat CTA */}
          <button
            onClick={() => { createNewChat(); setActiveTab('chat'); setSidebarOpen(false); }}
            className="flex items-center justify-center gap-2 w-full px-4 py-2.5 mb-5 rounded-xl text-sm font-semibold transition-all glow-ring"
            style={{ background: 'rgba(64,204,183,0.15)', border: '1px solid rgba(64,204,183,0.45)', color: '#40CCB7', fontFamily: "'Space Grotesk', sans-serif" }}
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Chat
          </button>

          {/* Primary nav */}
          <nav className="flex-1 flex flex-col gap-0.5">
            {[
              { id: 'analytics', icon: 'dashboard',   label: 'Analytics' },
              { id: 'chat',      icon: 'terminal',     label: 'SQL Chat' },
              { id: 'databases', icon: 'database',     label: 'Databases' },
              { id: 'tables',    icon: 'table_chart',  label: 'Tables' },
              { id: 'history',   icon: 'history',      label: 'History' },
            ].map(item => (
              <button
                key={item.id}
                onClick={() => { setActiveTab(item.id); setSidebarOpen(false); }}
                className={`nav-item w-full text-left ${activeTab === item.id ? 'active' : ''}`}
              >
                <span className="material-symbols-outlined text-[19px]" style={{ fontVariationSettings: activeTab === item.id ? "'FILL' 1" : "'FILL' 0" }}>{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>

          {/* Bottom section */}
          <div className="mt-4 pt-4 border-t border-outline flex flex-col gap-0.5">
            {[
              { id: 'settings', icon: 'settings',     label: 'Settings' },
              { id: 'support',  icon: 'help_outline',  label: 'Support' },
            ].map(item => (
              <button
                key={item.id}
                onClick={() => { setActiveTab(item.id); setSidebarOpen(false); }}
                className={`nav-item w-full text-left ${activeTab === item.id ? 'active' : ''}`}
              >
                <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: activeTab === item.id ? "'FILL' 1" : "'FILL' 0" }}>{item.icon}</span>
                {item.label}
              </button>
            ))}
            <button
              onClick={handleLogout}
              className="nav-item w-full text-left mt-1 text-error/70 hover:text-error hover:bg-error/8"
            >
              <span className="material-symbols-outlined text-[18px]">logout</span>
              Sign Out
            </button>
          </div>
        </aside>
        {/* ── Main Content Area ────────────────────────────────────────── */}
        <div className="flex-1 flex flex-col relative h-full overflow-hidden w-full" style={{ background: 'radial-gradient(ellipse 60% 40% at 80% 0%, rgba(64,204,183,0.04) 0%, transparent 70%), #101321' }}>
          <main className="flex-1 overflow-y-auto pb-32 scroll-smooth">
            <div className="max-w-[1000px] mx-auto w-full px-gutter pt-8 flex flex-col gap-8">
                {activeTab === 'chat' && (
                    <>
                        {chatHistory.length === 0 ? (
                            <div className="flex flex-col items-center justify-center mt-20 text-on-surface-variant/50">
                                <span className="material-symbols-outlined text-[64px] mb-4 text-primary/30">neurology</span>
                                <p className="font-body-lg text-body-lg text-on-surface">Ask me anything about your data.</p>
                                <p className="font-body-sm text-body-sm mt-2">Example: "Show me the top 5 customers by revenue"</p>
                            </div>
                        ) : (
                            chatHistory.map((msg, idx) => (
                                <div key={idx} className="animate-fade-up">
                                    {msg.role === 'user' ? (
                                        <div className="flex justify-end mb-6">
                                            <div className="text-white px-5 py-3.5 rounded-2xl rounded-tr-sm max-w-[75%] text-sm leading-relaxed shadow-lg" style={{ background: '#1C1E2D', border: '1px solid #2A2D3D' }}>
                                                {msg.content}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex items-start gap-3 max-w-[88%] mb-6">
                                            <div className="w-8 h-8 rounded-xl bg-primary/12 border border-primary/25 flex items-center justify-center shrink-0 mt-0.5">
                                                <span className="material-symbols-outlined text-primary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
                                            </div>
                                            <div className="flex flex-col gap-3 w-full min-w-0">
                                                <div className="text-white/90 text-sm leading-relaxed markdown-content pt-1">
                                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                        {msg.content}
                                                    </ReactMarkdown>
                                                </div>
                                                {msg.sql && (
                                                    <div className="rounded-xl overflow-hidden border border-outline shadow-xl mt-1">
                                                        <div className="flex items-center gap-2 px-4 py-2 border-b border-outline bg-background/70">
                                                            <span className="w-2.5 h-2.5 rounded-full bg-error/60" />
                                                            <span className="w-2.5 h-2.5 rounded-full bg-amber-400/60" />
                                                            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/60" />
                                                            <span className="ml-2 font-mono text-[11px] text-muted-foreground">SQL Query</span>
                                                        </div>
                                                        <div className="p-4 font-mono text-[12px] text-primary/80 leading-relaxed overflow-x-auto bg-black/40">
                                                            <pre><code>{msg.sql}</code></pre>
                                                        </div>
                                                    </div>
                                                )}
                                                {msg.data && renderTable(msg.data)}
                                                {msg.data && renderChart(msg.data)}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                        
                        {loading && (
                            <div className="flex items-start gap-3 max-w-[88%]">
                                <div className="w-8 h-8 rounded-xl bg-primary/12 border border-primary/25 flex items-center justify-center shrink-0">
                                    <span className="material-symbols-outlined text-primary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
                                </div>
                                <div className="flex items-center gap-1.5 h-9 px-4 rounded-xl border border-outline w-fit" style={{ background: '#1C1E2D' }}>
                                    <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-bounce" />
                                    <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-bounce" style={{ animationDelay: '0.18s' }} />
                                    <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-bounce" style={{ animationDelay: '0.36s' }} />
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </>
                )}

                {activeTab === 'analytics' && (<AnalyticsDashboard />)}
                {activeTab === 'databases' && (
                    <div className="flex flex-col mt-4">
                        <h2 className="font-display text-xl font-bold text-white mb-5">Connected Databases</h2>
                        <div className="flex items-center gap-4 p-5 rounded-2xl border border-outline hover:border-primary/30 transition-all" style={{ background: '#1C1E2D' }}>
                            <div className="w-11 h-11 rounded-xl bg-primary/12 border border-primary/25 flex items-center justify-center shrink-0">
                                <span className="material-symbols-outlined text-primary text-[22px]" style={{ fontVariationSettings: "'FILL' 1" }}>database</span>
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="font-display font-semibold text-white text-sm">{dbName || 'demo.db'}</p>
                                <p className="text-xs text-muted-foreground mt-0.5">Active connection</p>
                            </div>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-primary/10 border border-primary/25 text-primary">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                                Connected
                            </span>
                        </div>
                    </div>
                )}
                                {activeTab === 'history' && (
                    <div className="flex flex-col mt-4">
                        <h2 className="font-display text-headline-sm font-bold text-primary mb-6">Chat Sessions</h2>
                        {chats.length > 0 && chats.some(c => c.messages.length > 0) ? (
                            <div className="flex flex-col gap-4">
                                {chats.filter(c => c.messages.length > 0).map((chat) => (
                                    <div key={chat.id} onClick={() => { setActiveChatId(chat.id); setActiveTab('chat'); }} className="bg-surface-container-low/60 backdrop-blur-md rounded-xl border border-white/5 p-4 flex items-center gap-4 cursor-pointer hover:bg-white/[0.05] transition-all active:scale-[0.99] group">
                                        <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary transition-colors">chat_bubble</span>
                                        <div className="flex-1 overflow-hidden">
                                            <p className="font-body-lg text-on-surface group-hover:text-primary transition-colors truncate">{chat.title}</p>
                                            <p className="font-body-sm text-on-surface-variant truncate text-xs mt-1">{chat.messages.length} messages</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center mt-12 text-on-surface-variant/50">
                                <span className="material-symbols-outlined text-[64px] mb-4 text-primary/30">history</span>
                                <p className="font-body-lg text-body-lg text-on-surface">No history yet</p>
                                <p className="font-body-sm text-body-sm mt-2">Your past chat sessions will appear here.</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'tables' && (
                    <div className="flex flex-col mt-4">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="font-display text-headline-sm font-bold text-primary flex items-center gap-2">
                                <span className="material-symbols-outlined" style={{fontVariationSettings: "'FILL' 1"}}>table_chart</span>
                                Table Structure
                            </h2>
                            {tablesData.length > 0 && (
                                <span className="font-label-mono text-label-mono text-on-surface-variant bg-surface-container-highest px-3 py-1 rounded-full border border-white/10">
                                    {tablesData.length} table{tablesData.length !== 1 ? 's' : ''}
                                </span>
                            )}
                        </div>

                        {loadingTables && (
                            <div className="flex flex-col gap-4">
                                {[1, 2, 3].map(i => (
                                    <div key={i} className="bg-surface-container-low/60 rounded-2xl border border-white/5 p-5 animate-pulse">
                                        <div className="flex items-center gap-3 mb-4">
                                            <div className="w-8 h-8 rounded-lg bg-white/5" />
                                            <div className="h-4 bg-white/5 rounded w-40" />
                                            <div className="ml-auto h-5 bg-white/5 rounded-full w-20" />
                                        </div>
                                        <div className="flex flex-col gap-2">
                                            {[1,2,3].map(j => <div key={j} className="h-10 bg-white/5 rounded-lg" />)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {!loadingTables && tablesError && (
                            <div className="flex items-center gap-3 px-5 py-4 rounded-xl bg-error/10 border border-error/20 text-error">
                                <span className="material-symbols-outlined text-[20px]">error</span>
                                <p className="text-sm">{tablesError}</p>
                            </div>
                        )}

                        {!loadingTables && !tablesError && tablesData.length === 0 && (
                            <div className="flex flex-col items-center justify-center mt-20 text-on-surface-variant/50">
                                <span className="material-symbols-outlined text-[64px] mb-4 text-primary/30">table_chart</span>
                                <p className="font-body-lg text-body-lg text-on-surface">No tables found</p>
                                <p className="font-body-sm text-body-sm mt-2">Your database appears to be empty.</p>
                            </div>
                        )}

                        {!loadingTables && !tablesError && tablesData.length > 0 && (
                            <div className="flex flex-col gap-4">
                                {tablesData.map((table) => {
                                    const isOpen = expandedTable === table.full_name;
                                    return (
                                        <div key={table.full_name} className="bg-surface-container-low/60 backdrop-blur-md rounded-2xl border border-white/8 overflow-hidden hover:border-primary/20 transition-all duration-200">
                                            {/* Table header */}
                                            <button
                                                onClick={() => setExpandedTable(isOpen ? null : table.full_name)}
                                                className="w-full flex items-center gap-3 px-5 py-4 hover:bg-white/[0.03] transition-colors text-left"
                                            >
                                                <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                                                    <span className="material-symbols-outlined text-primary text-[16px]" style={{fontVariationSettings: "'FILL' 1"}}>table_chart</span>
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <span className="font-display font-semibold text-on-surface text-base truncate block">{table.full_name}</span>
                                                    {table.schema_name && (
                                                        <span className="font-label-mono text-label-mono text-on-surface-variant/60 text-[11px]">schema: {table.schema_name}</span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2 shrink-0">
                                                    <span className="font-label-mono text-[11px] text-on-surface-variant bg-surface-container-highest px-2.5 py-1 rounded-full border border-white/10">
                                                        {table.columns.length} col{table.columns.length !== 1 ? 's' : ''}
                                                    </span>
                                                    {table.primary_key.length > 0 && (
                                                        <span className="font-label-mono text-[11px] text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2.5 py-1 rounded-full">
                                                            PK
                                                        </span>
                                                    )}
                                                    {table.foreign_keys.length > 0 && (
                                                        <span className="font-label-mono text-[11px] text-sky-400 bg-sky-400/10 border border-sky-400/20 px-2.5 py-1 rounded-full">
                                                            FK
                                                        </span>
                                                    )}
                                                    <span className={`material-symbols-outlined text-on-surface-variant text-[20px] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>expand_more</span>
                                                </div>
                                            </button>

                                            {/* Columns table */}
                                            {isOpen && (
                                                <div className="border-t border-white/5">
                                                    {/* Column rows */}
                                                    <div className="overflow-x-auto">
                                                        <table className="w-full text-left">
                                                            <thead>
                                                                <tr className="bg-surface-container/50 border-b border-white/5">
                                                                    <th className="px-5 py-2.5 font-label-mono text-[11px] uppercase tracking-widest text-on-surface-variant/60 font-medium">Column</th>
                                                                    <th className="px-5 py-2.5 font-label-mono text-[11px] uppercase tracking-widest text-on-surface-variant/60 font-medium">Type</th>
                                                                    <th className="px-5 py-2.5 font-label-mono text-[11px] uppercase tracking-widest text-on-surface-variant/60 font-medium">Attributes</th>
                                                                    <th className="px-5 py-2.5 font-label-mono text-[11px] uppercase tracking-widest text-on-surface-variant/60 font-medium">Default</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-white/5">
                                                                {table.columns.map((col) => (
                                                                    <tr key={col.name} className="hover:bg-white/[0.025] transition-colors group">
                                                                        <td className="px-5 py-3">
                                                                            <div className="flex items-center gap-2">
                                                                                {col.primary_key && (
                                                                                    <span className="material-symbols-outlined text-amber-400 text-[14px]" title="Primary Key" style={{fontVariationSettings: "'FILL' 1"}}>key</span>
                                                                                )}
                                                                                <span className={`font-label-mono text-sm ${col.primary_key ? 'text-amber-300 font-semibold' : 'text-on-surface'}`}>{col.name}</span>
                                                                            </div>
                                                                        </td>
                                                                        <td className="px-5 py-3">
                                                                            <span className="font-label-mono text-[12px] text-secondary/80 bg-secondary/5 border border-secondary/15 px-2 py-0.5 rounded">{col.type}</span>
                                                                        </td>
                                                                        <td className="px-5 py-3">
                                                                            <div className="flex items-center gap-1.5 flex-wrap">
                                                                                {!col.nullable && (
                                                                                    <span className="font-label-mono text-[10px] text-rose-400 bg-rose-400/10 border border-rose-400/20 px-2 py-0.5 rounded-full">NOT NULL</span>
                                                                                )}
                                                                                {col.nullable && (
                                                                                    <span className="font-label-mono text-[10px] text-on-surface-variant/50 bg-white/5 border border-white/10 px-2 py-0.5 rounded-full">NULLABLE</span>
                                                                                )}
                                                                                {col.primary_key && (
                                                                                    <span className="font-label-mono text-[10px] text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-0.5 rounded-full">PRIMARY KEY</span>
                                                                                )}
                                                                            </div>
                                                                        </td>
                                                                        <td className="px-5 py-3">
                                                                            {col.default != null ? (
                                                                                <span className="font-label-mono text-[11px] text-on-surface-variant/70">{col.default}</span>
                                                                            ) : (
                                                                                <span className="text-on-surface-variant/30 text-xs">—</span>
                                                                            )}
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>

                                                    {/* FK & Index info */}
                                                    {(table.foreign_keys.length > 0 || table.indexes.length > 0) && (
                                                        <div className="border-t border-white/5 px-5 py-4 flex flex-wrap gap-6">
                                                            {table.foreign_keys.length > 0 && (
                                                                <div className="flex-1 min-w-[200px]">
                                                                    <p className="font-label-mono text-[10px] uppercase tracking-widest text-sky-400/70 mb-2">Foreign Keys</p>
                                                                    <div className="flex flex-col gap-1.5">
                                                                        {table.foreign_keys.map((fk, i) => (
                                                                            <div key={i} className="flex items-center gap-2 text-[12px] font-label-mono text-on-surface-variant">
                                                                                <span className="text-sky-400">{fk.constrained_columns.join(', ')}</span>
                                                                                <span className="material-symbols-outlined text-[12px] text-on-surface-variant/40">arrow_forward</span>
                                                                                <span className="text-on-surface-variant/70">{fk.referred_table}.{fk.referred_columns.join(', ')}</span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {table.indexes.length > 0 && (
                                                                <div className="flex-1 min-w-[200px]">
                                                                    <p className="font-label-mono text-[10px] uppercase tracking-widest text-purple-400/70 mb-2">Indexes</p>
                                                                    <div className="flex flex-col gap-1.5">
                                                                        {table.indexes.map((idx, i) => (
                                                                            <div key={i} className="flex items-center gap-2 text-[12px] font-label-mono text-on-surface-variant">
                                                                                <span className="material-symbols-outlined text-purple-400 text-[12px]">bolt</span>
                                                                                <span>{idx.name || '(unnamed)'}</span>
                                                                                <span className="text-on-surface-variant/50">({idx.columns.join(', ')})</span>
                                                                                {idx.unique && <span className="text-purple-400/80 text-[10px] bg-purple-400/10 border border-purple-400/20 px-1.5 py-0.5 rounded-full">UNIQUE</span>}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'settings' && (
                    <div className="flex flex-col mt-4 max-w-2xl">
                        <h2 className="font-display text-headline-sm font-bold text-primary mb-6 flex items-center gap-2"><span className="material-symbols-outlined">settings</span> Settings</h2>
                        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6 flex flex-col gap-6">
                            
                            <div>
                              <label className="block text-sm font-medium text-on-surface-variant mb-2">Anthropic API Key</label>
                              <p className="text-xs text-on-surface-variant/70 mb-3">If provided, this key will be used instead of the server's default key.</p>
                              <input 
                                type="password" 
                                value={apiKey} 
                                onChange={(e) => setApiKey(e.target.value)} 
                                placeholder="sk-ant-api03-..." 
                                className="w-full bg-surface-container-high border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all font-label-mono text-sm"
                              />
                            </div>

                            <hr className="border-white/5" />

                            <div>
                              <h3 className="text-on-surface font-medium mb-3">Theme Preferences</h3>
                              <div className="flex gap-4">
                                <button className="flex-1 py-3 rounded-xl border-2 border-primary bg-primary/10 text-primary font-medium flex items-center justify-center gap-2">
                                  <span className="material-symbols-outlined">dark_mode</span> Dark
                                </button>
                                <button className="flex-1 py-3 rounded-xl border-2 border-white/5 bg-surface-container-high text-on-surface-variant font-medium flex items-center justify-center gap-2 opacity-50 cursor-not-allowed">
                                  <span className="material-symbols-outlined">light_mode</span> Light (Soon)
                                </button>
                              </div>
                            </div>
                        </div>
                    </div>
                )}
                {activeTab === 'support' && (
                    <div className="flex flex-col mt-4 max-w-3xl">
                        <h2 className="font-display text-headline-sm font-bold text-primary mb-6 flex items-center gap-2"><span className="material-symbols-outlined">help_outline</span> Support Center</h2>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                          <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6">
                            <span className="material-symbols-outlined text-secondary text-[32px] mb-4">mail</span>
                            <h3 className="text-on-surface font-medium text-lg mb-2">Contact Us</h3>
                            <p className="text-on-surface-variant text-sm mb-4">Need direct assistance? Our team is here to help you get the most out of QueryTalk AI.</p>
                            <button className="bg-secondary-container text-on-secondary-container px-4 py-2 rounded-lg font-medium text-sm hover:bg-secondary-container/90 transition-colors">Email Support</button>
                          </div>
                          <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6">
                            <span className="material-symbols-outlined text-tertiary-container text-[32px] mb-4">book</span>
                            <h3 className="text-on-surface font-medium text-lg mb-2">Documentation</h3>
                            <p className="text-on-surface-variant text-sm mb-4">Read our detailed guides on database connections, query optimization, and more.</p>
                            <button className="bg-surface-container-high text-on-surface border border-white/10 px-4 py-2 rounded-lg font-medium text-sm hover:bg-surface-variant transition-colors">View Docs</button>
                          </div>
                        </div>

                        <h3 className="font-display text-title-lg font-medium text-on-surface mb-4 mt-4">Frequently Asked Questions</h3>
                        <div className="flex flex-col gap-3">
                          <div className="bg-surface-container-high/50 rounded-xl p-4 border border-white/5">
                            <h4 className="text-on-surface font-medium mb-2">How is my API key stored?</h4>
                            <p className="text-on-surface-variant text-sm leading-relaxed">Your API key is stored locally in your browser's localStorage and is sent securely via headers to our backend. It is never persisted in our database.</p>
                          </div>
                          <div className="bg-surface-container-high/50 rounded-xl p-4 border border-white/5">
                            <h4 className="text-on-surface font-medium mb-2">What databases are supported?</h4>
                            <p className="text-on-surface-variant text-sm leading-relaxed">Currently, we support SQLite, PostgreSQL, and MySQL. We are constantly working on adding more database integrations.</p>
                          </div>
                        </div>
                    </div>
                )}


                
            
                {activeTab === 'settings' && (
                    <div className="flex flex-col mt-4 max-w-2xl">
                        <h2 className="font-display text-headline-sm font-bold text-primary mb-6 flex items-center gap-2"><span className="material-symbols-outlined">settings</span> Settings</h2>
                        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6 flex flex-col gap-6">
                            
                            <div>
                              <label className="block text-sm font-medium text-on-surface-variant mb-2">Anthropic API Key</label>
                              <p className="text-xs text-on-surface-variant/70 mb-3">If provided, this key will be used instead of the server's default key.</p>
                              <input 
                                type="password" 
                                value={apiKey} 
                                onChange={(e) => setApiKey(e.target.value)} 
                                placeholder="sk-ant-api03-..." 
                                className="w-full bg-surface-container-high border border-white/10 rounded-xl px-4 py-3 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/50 transition-all font-label-mono text-sm"
                              />
                            </div>

                            <hr className="border-white/5" />

                            <div>
                              <h3 className="text-on-surface font-medium mb-3">Theme Preferences</h3>
                              <div className="flex gap-4">
                                <button className="flex-1 py-3 rounded-xl border-2 border-primary bg-primary/10 text-primary font-medium flex items-center justify-center gap-2">
                                  <span className="material-symbols-outlined">dark_mode</span> Dark
                                </button>
                                <button className="flex-1 py-3 rounded-xl border-2 border-white/5 bg-surface-container-high text-on-surface-variant font-medium flex items-center justify-center gap-2 opacity-50 cursor-not-allowed">
                                  <span className="material-symbols-outlined">light_mode</span> Light (Soon)
                                </button>
                              </div>
                            </div>
                        </div>
                    </div>
                )}
                {activeTab === 'support' && (
                    <div className="flex flex-col mt-4 max-w-3xl">
                        <h2 className="font-display text-headline-sm font-bold text-primary mb-6 flex items-center gap-2"><span className="material-symbols-outlined">help_outline</span> Support Center</h2>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                          <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6">
                            <span className="material-symbols-outlined text-secondary text-[32px] mb-4">mail</span>
                            <h3 className="text-on-surface font-medium text-lg mb-2">Contact Us</h3>
                            <p className="text-on-surface-variant text-sm mb-4">Need direct assistance? Our team is here to help you get the most out of QueryTalk AI.</p>
                            <button className="bg-secondary-container text-on-secondary-container px-4 py-2 rounded-lg font-medium text-sm hover:bg-secondary-container/90 transition-colors">Email Support</button>
                          </div>
                          <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6">
                            <span className="material-symbols-outlined text-tertiary-container text-[32px] mb-4">book</span>
                            <h3 className="text-on-surface font-medium text-lg mb-2">Documentation</h3>
                            <p className="text-on-surface-variant text-sm mb-4">Read our detailed guides on database connections, query optimization, and more.</p>
                            <button className="bg-surface-container-high text-on-surface border border-white/10 px-4 py-2 rounded-lg font-medium text-sm hover:bg-surface-variant transition-colors">View Docs</button>
                          </div>
                        </div>

                        <h3 className="font-display text-title-lg font-medium text-on-surface mb-4 mt-4">Frequently Asked Questions</h3>
                        <div className="flex flex-col gap-3">
                          <div className="bg-surface-container-high/50 rounded-xl p-4 border border-white/5">
                            <h4 className="text-on-surface font-medium mb-2">How is my API key stored?</h4>
                            <p className="text-on-surface-variant text-sm leading-relaxed">Your API key is stored locally in your browser's localStorage and is sent securely via headers to our backend. It is never persisted in our database.</p>
                          </div>
                          <div className="bg-surface-container-high/50 rounded-xl p-4 border border-white/5">
                            <h4 className="text-on-surface font-medium mb-2">What databases are supported?</h4>
                            <p className="text-on-surface-variant text-sm leading-relaxed">Currently, we support SQLite, PostgreSQL, and MySQL. We are constantly working on adding more database integrations.</p>
                          </div>
                        </div>
                    </div>
                )}
            
                {activeTab === 'notifications' && (
                    <div className="flex flex-col mt-4 max-w-2xl">
                        <h2 className="font-display text-headline-sm font-bold text-primary mb-6 flex items-center gap-2"><span className="material-symbols-outlined">notifications</span> Notifications</h2>
                        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6 flex flex-col gap-4">
                            <div className="flex gap-4 items-start pb-4 border-b border-white/5">
                                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary shrink-0">
                                    <span className="material-symbols-outlined">database</span>
                                </div>
                                <div>
                                    <h3 className="text-on-surface font-medium">Database Connected</h3>
                                    <p className="text-on-surface-variant text-sm mt-1">Successfully connected to local SQLite database (demo_v2.db).</p>
                                    <span className="text-xs text-on-surface-variant/50 mt-2 block">Just now</span>
                                </div>
                            </div>
                            <div className="flex gap-4 items-start pb-4 border-b border-white/5">
                                <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center text-secondary shrink-0">
                                    <span className="material-symbols-outlined">analytics</span>
                                </div>
                                <div>
                                    <h3 className="text-on-surface font-medium">Analytics Updated</h3>
                                    <p className="text-on-surface-variant text-sm mt-1">Your dashboard data has been successfully seeded with 500 records.</p>
                                    <span className="text-xs text-on-surface-variant/50 mt-2 block">2 minutes ago</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                {activeTab === 'security' && (
                    <div className="flex flex-col mt-4 max-w-2xl">
                        <h2 className="font-display text-headline-sm font-bold text-primary mb-6 flex items-center gap-2"><span className="material-symbols-outlined">shield</span> Security & Access</h2>
                        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-6 flex flex-col gap-6">
                            <div>
                                <h3 className="text-on-surface font-medium mb-2">Connection Encryption</h3>
                                <p className="text-on-surface-variant text-sm mb-4">All queries are executed securely over authenticated sessions. Your API keys are encrypted at rest.</p>
                                <div className="flex items-center gap-2 text-primary">
                                    <span className="material-symbols-outlined text-[20px]">lock</span>
                                    <span className="text-sm font-medium">End-to-End Encrypted</span>
                                </div>
                            </div>
                            <hr className="border-white/5" />
                            <div>
                                <h3 className="text-on-surface font-medium mb-2">Query Safety</h3>
                                <p className="text-on-surface-variant text-sm mb-4">QueryTalk AI strictly generates READ-ONLY SQL queries. Write, Update, and Delete operations are blocked at the middleware layer.</p>
                                <div className="flex items-center gap-2 text-secondary">
                                    <span className="material-symbols-outlined text-[20px]">verified_user</span>
                                    <span className="text-sm font-medium">Safe Mode Active</span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </main>
        
        {activeTab === 'chat' && (
            <div className="absolute bottom-0 left-0 w-full px-4 md:px-8 pb-5 md:pb-7 pt-14 bg-gradient-to-t from-background via-background/90 to-transparent pointer-events-none">
                <div className="max-w-[860px] mx-auto pointer-events-auto">
                    <form
                        onSubmit={handleSend}
                        className="flex items-center gap-2 p-2 rounded-2xl border border-outline backdrop-blur-xl shadow-[0_8px_40px_rgba(0,0,0,0.5)] focus-within:border-primary/40 focus-within:shadow-[0_8px_40px_rgba(0,0,0,0.5),0_0_0_1px_rgba(64,204,183,0.15)] transition-all"
                        style={{ background: 'rgba(28,30,45,0.92)' }}
                    >
                        <input
                            id="chat-input"
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                            className="flex-1 bg-transparent border-none focus:ring-0 text-white text-sm placeholder:text-muted-foreground pl-3 pr-2"
                            placeholder="Ask anything about your data…"
                            autoComplete="off"
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            id="chat-send-btn"
                            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed glow-ring"
                            style={{ background: 'rgba(64,204,183,0.25)', border: '1px solid #40CCB7', color: '#40CCB7' }}
                        >
                            <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>send</span>
                        </button>
                    </form>
                    <p className="text-center mt-2 text-[11px] font-mono text-muted-foreground/50">
                        QueryTalk AI may make mistakes — verify critical data independently.
                    </p>
                </div>
            </div>
        )}
      </div>
    </div>
    </div>
  );
}

function PreviewTable({ data }) {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  if (!data || data.length === 0) return null;
  const keys = Object.keys(data[0]);

  const totalRows = data.length;
  const totalPages = Math.ceil(totalRows / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalRows);
  const paginatedData = data.slice(startIndex, endIndex);

  return (
    <div className="bg-surface-container-low/60 backdrop-blur-md rounded-xl border border-white/5 overflow-hidden mt-4">
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[18px]">table_chart</span>
          <span className="font-body-sm text-body-sm font-medium text-on-surface">Data Preview</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-[#1C1E2D] border border-white/10 rounded-lg px-2 py-1 text-on-surface focus:outline-none focus:border-primary text-xs"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          <span className="text-xs font-mono text-muted-foreground bg-white/5 px-2.5 py-0.5 rounded-full border border-white/10">
            {totalRows} row{totalRows !== 1 ? 's' : ''}
          </span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left font-body-sm text-body-sm">
          <thead>
            <tr className="border-b border-white/5 bg-surface-container/30">
              {keys.map(k => (
                <th key={k} className="px-4 py-3 font-medium text-on-surface-variant">{k}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {paginatedData.map((row, i) => (
              <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                {keys.map(k => (
                  <td key={k} className="px-4 py-3 text-on-surface">{row[k]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-white/5 flex items-center justify-between bg-surface-container/10 font-body-sm text-xs text-muted-foreground">
          <div>
            Showing <span className="text-on-surface font-medium">{startIndex + 1}-{endIndex}</span> of <span className="text-on-surface font-medium">{totalRows}</span> rows
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="w-8 h-8 rounded-lg flex items-center justify-center border border-white/10 bg-white/5 text-on-surface hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none transition-all"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_left</span>
            </button>
            <span className="font-mono">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="w-8 h-8 rounded-lg flex items-center justify-center border border-white/10 bg-white/5 text-on-surface hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none transition-all"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
