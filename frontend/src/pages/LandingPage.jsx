import { useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';

/* ── Tiny hook: run callback when element enters viewport ── */
function useInView(threshold = 0.15) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setInView(true); obs.disconnect(); }
    }, { threshold });
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, inView];
}

/* ── Reusable fade-in wrapper ── */
function Reveal({ children, delay = 0, className = '' }) {
  const [ref, inView] = useInView();
  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: inView ? 1 : 0,
        transform: inView ? 'translateY(0)' : 'translateY(28px)',
        transition: `opacity 0.7s ease ${delay}ms, transform 0.7s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

/* ── SQL typing animation ── */
const SQL_LINES = [
  { prompt: 'You', text: 'Show me the top 10 customers by revenue this quarter' },
  { prompt: 'AI', text: 'SELECT customer_name, SUM(amount) AS revenue\nFROM orders\nWHERE date >= DATE_TRUNC(\'quarter\', NOW())\nGROUP BY customer_name\nORDER BY revenue DESC\nLIMIT 10;', isSQL: true },
];

function TypingDemo() {
  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (done) return;
    const current = SQL_LINES[lineIdx];
    if (!current) return;
    if (charIdx < current.text.length) {
      const t = setTimeout(() => setCharIdx(c => c + 1), current.isSQL ? 18 : 30);
      return () => clearTimeout(t);
    }
    if (lineIdx < SQL_LINES.length - 1) {
      const t = setTimeout(() => { setLineIdx(l => l + 1); setCharIdx(0); }, 600);
      return () => clearTimeout(t);
    }
    setDone(true);
  }, [lineIdx, charIdx, done]);

  const displayed = SQL_LINES.slice(0, lineIdx + 1).map((line, i) => ({
    ...line,
    text: i === lineIdx ? line.text.slice(0, charIdx) : line.text,
  }));

  return (
    <div className="w-full rounded-2xl overflow-hidden border border-outline shadow-[0_0_60px_rgba(64,204,183,0.12)]">
      {/* Terminal chrome */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-outline" style={{ background: '#0C0E1A' }}>
        <span className="w-3 h-3 rounded-full bg-red-500/70" />
        <span className="w-3 h-3 rounded-full bg-yellow-400/70" />
        <span className="w-3 h-3 rounded-full bg-green-500/70" />
        <span className="ml-3 font-mono text-xs text-muted-foreground">querytalk — sql-chat</span>
      </div>
      <div className="p-6 flex flex-col gap-5 min-h-[280px]" style={{ background: '#0F1221' }}>
        {displayed.map((line, i) => (
          <div key={i} className={`flex gap-3 ${line.isSQL ? '' : ''}`}>
            <span
              className="text-xs font-mono font-bold mt-0.5 shrink-0"
              style={{ color: line.prompt === 'AI' ? '#40CCB7' : '#9CA3AF' }}
            >
              {line.prompt === 'AI' ? '⬡ AI' : '→ You'}
            </span>
            <div className="flex-1 min-w-0">
              {line.isSQL ? (
                <pre className="font-mono text-sm leading-relaxed whitespace-pre-wrap text-primary/90">
                  {line.text}
                  {i === lineIdx && !done && (
                    <span className="inline-block w-0.5 h-4 bg-primary ml-0.5 align-middle animate-pulse" />
                  )}
                </pre>
              ) : (
                <p className="text-white/90 text-sm leading-relaxed">
                  {line.text}
                  {i === lineIdx && !done && (
                    <span className="inline-block w-0.5 h-4 bg-white/50 ml-0.5 align-middle animate-pulse" />
                  )}
                </p>
              )}
            </div>
          </div>
        ))}
        {done && (
          <div className="flex items-center gap-2 mt-2 px-3 py-2 rounded-lg" style={{ background: 'rgba(64,204,183,0.08)', border: '1px solid rgba(64,204,183,0.2)' }}>
            <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
            <span className="text-xs font-mono text-primary">Query executed — 10 rows returned in 12ms</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Stat counter ── */
function StatCard({ value, label, suffix = '' }) {
  const [ref, inView] = useInView(0.3);
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!inView) return;
    const num = parseInt(value);
    const step = Math.ceil(num / 60);
    let cur = 0;
    const t = setInterval(() => {
      cur = Math.min(cur + step, num);
      setCount(cur);
      if (cur >= num) clearInterval(t);
    }, 20);
    return () => clearInterval(t);
  }, [inView, value]);

  return (
    <div ref={ref} className="flex flex-col items-center text-center">
      <p className="font-display font-bold text-white" style={{ fontSize: '3rem', lineHeight: 1, letterSpacing: '-0.03em' }}>
        {inView ? count : 0}{suffix}
      </p>
      <p className="text-muted-foreground text-sm mt-2">{label}</p>
    </div>
  );
}

/* ── Feature card ── */
function FeatureCard({ icon, title, description, delay, img }) {
  return (
    <Reveal delay={delay}>
      <div
        className="rounded-2xl p-6 flex flex-col gap-4 h-full transition-all duration-300 group cursor-default"
        style={{ background: '#1C1E2D', border: '1px solid #2A2D3D' }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(64,204,183,0.35)'; e.currentTarget.style.boxShadow = '0 0 30px rgba(64,204,183,0.1)'; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = '#2A2D3D'; e.currentTarget.style.boxShadow = 'none'; }}
      >
        {img && (
          <div className="w-full h-40 rounded-xl overflow-hidden mb-1">
            <img src={img} alt={title} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
          </div>
        )}
        <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style={{ background: 'rgba(64,204,183,0.12)', border: '1px solid rgba(64,204,183,0.25)' }}>
          <span className="material-symbols-outlined text-primary text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>{icon}</span>
        </div>
        <div>
          <h3 className="font-display font-semibold text-white text-base mb-1.5">{title}</h3>
          <p className="text-muted-foreground text-sm leading-relaxed">{description}</p>
        </div>
      </div>
    </Reveal>
  );
}

/* ── Step card ── */
function Step({ num, icon, title, desc, delay }) {
  return (
    <Reveal delay={delay}>
      <div className="flex flex-col items-center text-center gap-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(64,204,183,0.1)', border: '1px solid rgba(64,204,183,0.3)' }}>
            <span className="material-symbols-outlined text-primary text-[28px]" style={{ fontVariationSettings: "'FILL' 1" }}>{icon}</span>
          </div>
          <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary flex items-center justify-center text-[11px] font-mono font-bold" style={{ color: '#002E28' }}>{num}</span>
        </div>
        <div>
          <h3 className="font-display font-semibold text-white text-base mb-1">{title}</h3>
          <p className="text-muted-foreground text-sm leading-relaxed max-w-[200px] mx-auto">{desc}</p>
        </div>
      </div>
    </Reveal>
  );
}

/* ── Pricing card ── */
function PricingCard({ plan, price, period, features, cta, highlight, delay, onCTA }) {
  return (
    <Reveal delay={delay}>
      <div
        className="rounded-2xl p-7 flex flex-col gap-6 h-full relative transition-all duration-300"
        style={{
          background: highlight ? 'rgba(64,204,183,0.07)' : '#1C1E2D',
          border: highlight ? '1px solid rgba(64,204,183,0.4)' : '1px solid #2A2D3D',
          boxShadow: highlight ? '0 0 40px rgba(64,204,183,0.15)' : 'none',
        }}
      >
        {highlight && (
          <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-[11px] font-mono font-bold uppercase tracking-widest" style={{ background: '#40CCB7', color: '#002E28' }}>
            Most Popular
          </span>
        )}
        <div>
          <p className="font-mono text-xs text-muted-foreground uppercase tracking-widest mb-3">{plan}</p>
          <div className="flex items-end gap-1.5">
            <span className="font-display font-bold text-white" style={{ fontSize: '2.5rem', lineHeight: 1 }}>{price}</span>
            {period && <span className="text-muted-foreground text-sm mb-1">/{period}</span>}
          </div>
        </div>
        <ul className="flex flex-col gap-2.5 flex-1">
          {features.map((f, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm">
              <span className="material-symbols-outlined text-primary text-[16px] mt-0.5 shrink-0">check</span>
              <span className={f.muted ? 'text-muted-foreground' : 'text-white/85'}>{f.text}</span>
            </li>
          ))}
        </ul>
        <button
          onClick={onCTA}
          className="w-full py-3 rounded-xl text-sm font-semibold font-display transition-all duration-200"
          style={highlight
            ? { background: '#40CCB7', color: '#002E28', border: 'none' }
            : { background: 'rgba(64,204,183,0.12)', border: '1px solid rgba(64,204,183,0.35)', color: '#40CCB7' }
          }
          onMouseEnter={e => { if (highlight) e.currentTarget.style.opacity = '0.88'; else e.currentTarget.style.background = 'rgba(64,204,183,0.2)'; }}
          onMouseLeave={e => { if (highlight) e.currentTarget.style.opacity = '1'; else e.currentTarget.style.background = 'rgba(64,204,183,0.12)'; }}
        >
          {cta}
        </button>
      </div>
    </Reveal>
  );
}

/* ── Testimonial ── */
function Testimonial({ quote, name, title, delay }) {
  return (
    <Reveal delay={delay}>
      <div className="rounded-2xl p-6 flex flex-col gap-4 h-full" style={{ background: '#1C1E2D', border: '1px solid #2A2D3D' }}>
        <div className="flex gap-0.5">
          {[...Array(5)].map((_, i) => (
            <span key={i} className="material-symbols-outlined text-primary text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
          ))}
        </div>
        <p className="text-white/80 text-sm leading-relaxed flex-1">"{quote}"</p>
        <div className="flex items-center gap-3 pt-2 border-t border-outline">
          <div className="w-8 h-8 rounded-full flex items-center justify-center font-display font-bold text-xs" style={{ background: 'rgba(64,204,183,0.2)', color: '#40CCB7' }}>
            {name[0]}
          </div>
          <div>
            <p className="font-display font-semibold text-white text-sm">{name}</p>
            <p className="text-muted-foreground text-xs">{title}</p>
          </div>
        </div>
      </div>
    </Reveal>
  );
}

/* ══════════════════════════════════════════════════════════
   MAIN LANDING PAGE
══════════════════════════════════════════════════════════ */
export default function LandingPage() {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    setMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen antialiased overflow-x-hidden" style={{ background: '#101321', color: '#fff' }}>

      {/* ─────────────────────────────────────────────────────────
          NAVBAR
      ───────────────────────────────────────────────────────── */}
      <nav
        className="fixed top-0 inset-x-0 z-50 transition-all duration-300"
        style={{
          background: scrolled ? 'rgba(16,19,33,0.92)' : 'transparent',
          backdropFilter: scrolled ? 'blur(20px)' : 'none',
          borderBottom: scrolled ? '1px solid #2A2D3D' : '1px solid transparent',
        }}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(64,204,183,0.15)', border: '1px solid rgba(64,204,183,0.35)' }}>
              <span className="material-symbols-outlined text-primary text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
            </div>
            <span className="font-display font-bold text-white text-lg">QueryTalk AI</span>
          </div>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {['features', 'how-it-works', 'pricing', 'testimonials'].map(id => (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:text-white hover:bg-white/5 transition-all capitalize"
              >
                {id.replace(/-/g, ' ')}
              </button>
            ))}
          </div>

          {/* CTA buttons */}
          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={() => navigate('/sign-in')}
              className="px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-white transition-colors"
            >
              Sign In
            </button>
            <button
              onClick={() => navigate('/sign-up')}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold font-display transition-all"
              style={{ background: 'rgba(64,204,183,0.18)', border: '1px solid #40CCB7', color: '#40CCB7' }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(64,204,183,0.3)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(64,204,183,0.25)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'rgba(64,204,183,0.18)'; e.currentTarget.style.boxShadow = 'none'; }}
            >
              Get Started Free
            </button>
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden w-9 h-9 flex items-center justify-center rounded-lg text-muted-foreground hover:text-white hover:bg-white/5 transition-all"
          >
            <span className="material-symbols-outlined">{mobileMenuOpen ? 'close' : 'menu'}</span>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-outline px-6 py-4 flex flex-col gap-1" style={{ background: 'rgba(16,19,33,0.98)' }}>
            {['features', 'how-it-works', 'pricing', 'testimonials'].map(id => (
              <button key={id} onClick={() => scrollTo(id)} className="text-left px-4 py-3 rounded-lg text-sm text-muted-foreground hover:text-white hover:bg-white/5 transition-all capitalize">
                {id.replace(/-/g, ' ')}
              </button>
            ))}
            <div className="flex gap-3 mt-3 pt-3 border-t border-outline">
              <button onClick={() => navigate('/sign-in')} className="flex-1 py-2.5 rounded-lg text-sm border border-outline text-muted-foreground hover:text-white transition-all">Sign In</button>
              <button onClick={() => navigate('/sign-up')} className="flex-1 py-2.5 rounded-xl text-sm font-semibold font-display" style={{ background: 'rgba(64,204,183,0.18)', border: '1px solid #40CCB7', color: '#40CCB7' }}>Get Started</button>
            </div>
          </div>
        )}
      </nav>

      {/* ─────────────────────────────────────────────────────────
          HERO
      ───────────────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 px-6 overflow-hidden">
        {/* Ambient glows */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full pointer-events-none" style={{ background: 'radial-gradient(ellipse, rgba(64,204,183,0.12) 0%, transparent 70%)', filter: 'blur(40px)' }} />
        <div className="absolute top-[20%] left-[5%] w-64 h-64 rounded-full pointer-events-none" style={{ background: 'rgba(64,204,183,0.05)', filter: 'blur(80px)' }} />
        <div className="absolute top-[30%] right-[5%] w-80 h-80 rounded-full pointer-events-none" style={{ background: 'rgba(64,204,183,0.04)', filter: 'blur(100px)' }} />

        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col items-center text-center gap-8">

            {/* Badge */}
            <Reveal>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-mono font-semibold" style={{ background: 'rgba(64,204,183,0.08)', border: '1px solid rgba(64,204,183,0.25)', color: '#40CCB7' }}>
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                Now in Public Beta · No credit card required
              </div>
            </Reveal>

            {/* Headline */}
            <Reveal delay={100}>
              <h1 className="font-display font-bold text-white leading-tight" style={{ fontSize: 'clamp(2.5rem, 6vw, 4.5rem)', letterSpacing: '-0.03em', maxWidth: '800px' }}>
                Query Any Database with{' '}
                <span style={{ color: '#40CCB7' }}>Plain English</span>
              </h1>
            </Reveal>

            {/* Sub */}
            <Reveal delay={200}>
              <p className="text-muted-foreground leading-relaxed max-w-2xl" style={{ fontSize: '1.125rem' }}>
                QueryTalk AI translates your natural language questions into precise SQL — instantly. Connect PostgreSQL, MySQL, SQLite or Snowflake and start getting answers in seconds, no SQL expertise required.
              </p>
            </Reveal>

            {/* CTA buttons */}
            <Reveal delay={300}>
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <button
                  onClick={() => navigate('/sign-up')}
                  id="hero-get-started-btn"
                  className="px-8 py-4 rounded-xl text-base font-bold font-display flex items-center gap-2 transition-all duration-200"
                  style={{ background: '#40CCB7', color: '#002E28' }}
                  onMouseEnter={e => { e.currentTarget.style.opacity = '0.88'; e.currentTarget.style.boxShadow = '0 0 30px rgba(64,204,183,0.4)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                  onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translateY(0)'; }}
                >
                  Start for Free
                  <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
                </button>
                <button
                  onClick={() => scrollTo('how-it-works')}
                  className="px-8 py-4 rounded-xl text-base font-semibold font-display flex items-center gap-2 transition-all duration-200"
                  style={{ background: 'transparent', border: '1px solid #2A2D3D', color: '#9CA3AF' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(64,204,183,0.35)'; e.currentTarget.style.color = '#fff'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = '#2A2D3D'; e.currentTarget.style.color = '#9CA3AF'; }}
                >
                  <span className="material-symbols-outlined text-[20px]">play_circle</span>
                  See How It Works
                </button>
              </div>
            </Reveal>

            {/* Trust line */}
            <Reveal delay={400}>
              <p className="text-xs font-mono text-muted-foreground/60">
                End-to-end encrypted · Read-only queries · SOC 2 ready
              </p>
            </Reveal>

            {/* Hero image — globe */}
            {/* <Reveal delay={250} className="w-full max-w-4xl mt-4">
              <div className="relative rounded-2xl overflow-hidden" style={{ border: '1px solid rgba(64,204,183,0.2)', boxShadow: '0 0 80px rgba(64,204,183,0.12)' }}>
                <img src="/hero_globe.png" alt="QueryTalk AI — Database intelligence visualization" className="w-full h-auto" />
                <div className="absolute inset-0" style={{ background: 'linear-gradient(to bottom, transparent 60%, #101321 100%)' }} />
              </div>
            </Reveal> */}
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          STATS BAR
      ───────────────────────────────────────────────────────── */}
      <section className="py-16 px-6" style={{ background: '#1C1E2D', borderTop: '1px solid #2A2D3D', borderBottom: '1px solid #2A2D3D' }}>
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          <StatCard value="50000" suffix="+" label="Queries executed" />
          <StatCard value="1200" suffix="+" label="Databases connected" />
          <StatCard value="98" suffix="%" label="Query accuracy" />
          <StatCard value="12" suffix="ms" label="Avg response time" />
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          LIVE DEMO
      ───────────────────────────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: '#101321' }}>
        <div className="max-w-5xl mx-auto">
          <Reveal className="text-center mb-14">
            <p className="text-xs font-mono text-primary uppercase tracking-widest mb-3">Live Demo</p>
            <h2 className="font-display font-bold text-white" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', letterSpacing: '-0.02em' }}>
              Ask in English. Get SQL instantly.
            </h2>
            <p className="text-muted-foreground mt-4 max-w-xl mx-auto leading-relaxed">
              Watch QueryTalk AI translate a natural language question into a precise, optimized SQL query in real time.
            </p>
          </Reveal>

          <div className="grid md:grid-cols-2 gap-6 items-center">
            <Reveal delay={100}>
              <TypingDemo />
            </Reveal>
            <Reveal delay={200} className="flex flex-col gap-5">
              {[
                { icon: 'translate', title: 'Understands context', desc: 'Knows your schema — tables, columns, relationships — so queries are always accurate.' },
                { icon: 'speed', title: 'Sub-second latency', desc: 'Get results in milliseconds. No waiting, no back-and-forth, just answers.' },
                { icon: 'shield', title: 'Read-only by default', desc: 'All generated queries are strictly SELECT — your data can never be mutated.' },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-4 p-4 rounded-xl transition-all" style={{ background: '#1C1E2D', border: '1px solid #2A2D3D' }}>
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ background: 'rgba(64,204,183,0.1)', border: '1px solid rgba(64,204,183,0.2)' }}>
                    <span className="material-symbols-outlined text-primary text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>{item.icon}</span>
                  </div>
                  <div>
                    <p className="font-display font-semibold text-white text-sm mb-1">{item.title}</p>
                    <p className="text-muted-foreground text-xs leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </Reveal>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          FEATURES
      ───────────────────────────────────────────────────────── */}
      <section id="features" className="py-24 px-6" style={{ background: '#1C1E2D', borderTop: '1px solid #2A2D3D' }}>
        <div className="max-w-6xl mx-auto">
          <Reveal className="text-center mb-16">
            <p className="text-xs font-mono text-primary uppercase tracking-widest mb-3">Features</p>
            <h2 className="font-display font-bold text-white" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', letterSpacing: '-0.02em' }}>
              Everything you need to query smarter
            </h2>
            <p className="text-muted-foreground mt-4 max-w-xl mx-auto">
              From natural language to analytics dashboards — QueryTalk AI gives your whole team superpowers over your data.
            </p>
          </Reveal>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <FeatureCard
              icon="psychology"
              title="Natural Language to SQL"
              description="Type questions like a human. Get back production-ready SQL. Our AI understands intent, not just keywords."
              delay={0}
              img="/feature_nlp.png"
            />
            <FeatureCard
              icon="hub"
              title="Multi-Database Support"
              description="Connect PostgreSQL, MySQL, SQLite and Snowflake. Switch between connections with a single click."
              delay={100}
              img="/feature_connections.png"
            />
            <FeatureCard
              icon="dashboard"
              title="Analytics Dashboard"
              description="Auto-generated charts and visualizations from your query results. No BI tool needed."
              delay={200}
            />
            <FeatureCard
              icon="table_chart"
              title="Schema Explorer"
              description="Browse every table, column, index and foreign key relationship in a clean visual interface."
              delay={300}
            />
            <FeatureCard
              icon="history"
              title="Query History"
              description="Every session is saved. Search, replay, and build on past queries across your team."
              delay={400}
            />
            <FeatureCard
              icon="lock"
              title="Enterprise Security"
              description="End-to-end encryption, read-only mode, Clerk authentication, and SOC 2 ready architecture."
              delay={500}
            />
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          DASHBOARD PREVIEW
      ───────────────────────────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: '#101321' }}>
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <Reveal>
              <p className="text-xs font-mono text-primary uppercase tracking-widest mb-4">The Interface</p>
              <h2 className="font-display font-bold text-white mb-5" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', letterSpacing: '-0.02em' }}>
                A workspace built for data professionals
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-8">
                QueryTalk AI isn't just a chatbot. It's a full data workspace with a beautiful dark interface, live analytics, schema browsing, and persistent chat history — designed to feel as premium as the tools you already love.
              </p>
              <ul className="flex flex-col gap-3">
                {[
                  'AI chat with SQL context awareness',
                  'Real-time analytics with auto-charts',
                  'Visual schema and table explorer',
                  'Persistent multi-session history',
                  'Responsive — works on any device',
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-sm text-white/80">
                    <span className="material-symbols-outlined text-primary text-[16px]">check_circle</span>
                    {item}
                  </li>
                ))}
              </ul>
            </Reveal>
            <Reveal delay={150}>
              <div className="rounded-2xl overflow-hidden" style={{ border: '1px solid rgba(64,204,183,0.2)', boxShadow: '0 0 60px rgba(64,204,183,0.1)' }}>
                <img src="/dashboard_mockup.png" alt="QueryTalk AI dashboard interface" className="w-full h-auto" />
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          HOW IT WORKS
      ───────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-24 px-6" style={{ background: '#1C1E2D', borderTop: '1px solid #2A2D3D', borderBottom: '1px solid #2A2D3D' }}>
        <div className="max-w-5xl mx-auto">
          <Reveal className="text-center mb-16">
            <p className="text-xs font-mono text-primary uppercase tracking-widest mb-3">How It Works</p>
            <h2 className="font-display font-bold text-white" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', letterSpacing: '-0.02em' }}>
              Up and running in under 2 minutes
            </h2>
          </Reveal>

          <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-8 relative">
            {/* Connector line */}
            <div className="hidden md:block absolute top-8 left-[12.5%] right-[12.5%] h-px" style={{ background: 'linear-gradient(to right, transparent, rgba(64,204,183,0.3), rgba(64,204,183,0.3), transparent)' }} />
            <Step num="1" icon="account_circle" title="Create Account" desc="Sign up free in seconds with email or Google." delay={0} />
            <Step num="2" icon="hub" title="Connect Database" desc="Add credentials for any supported database — we encrypt everything." delay={150} />
            <Step num="3" icon="chat" title="Ask a Question" desc="Type your question in plain English in the chat." delay={300} />
            <Step num="4" icon="insights" title="Get Answers" desc="Get back SQL, data, and auto-generated charts instantly." delay={450} />
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          TESTIMONIALS
      ───────────────────────────────────────────────────────── */}
      <section id="testimonials" className="py-24 px-6" style={{ background: '#101321' }}>
        <div className="max-w-6xl mx-auto">
          <Reveal className="text-center mb-16">
            <p className="text-xs font-mono text-primary uppercase tracking-widest mb-3">Testimonials</p>
            <h2 className="font-display font-bold text-white" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', letterSpacing: '-0.02em' }}>
              Loved by data teams everywhere
            </h2>
          </Reveal>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <Testimonial
              quote="This is the first AI tool that actually understands our schema. We went from spending hours writing reports to getting answers in seconds."
              name="Sarah Chen"
              title="Head of Analytics, Fintech Startup"
              delay={0}
            />
            <Testimonial
              quote="Non-technical stakeholders can now query our Postgres database without ever writing a line of SQL. Game changer."
              name="Marcus Webb"
              title="CTO, E-commerce Platform"
              delay={100}
            />
            <Testimonial
              quote="The schema explorer alone is worth it. But the AI chat is what makes us ship 3x faster on data tasks."
              name="Priya Nair"
              title="Senior Data Engineer"
              delay={200}
            />
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          PRICING
      ───────────────────────────────────────────────────────── */}
      <section id="pricing" className="py-24 px-6" style={{ background: '#1C1E2D', borderTop: '1px solid #2A2D3D' }}>
        <div className="max-w-5xl mx-auto">
          <Reveal className="text-center mb-16">
            <p className="text-xs font-mono text-primary uppercase tracking-widest mb-3">Pricing</p>
            <h2 className="font-display font-bold text-white" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', letterSpacing: '-0.02em' }}>
              Simple, transparent pricing
            </h2>
            <p className="text-muted-foreground mt-4">Start free. Scale when you're ready. No surprise fees.</p>
          </Reveal>

          <div className="grid md:grid-cols-3 gap-6">
            <PricingCard
              plan="Starter"
              price="Free"
              features={[
                { text: '1 database connection' },
                { text: '100 queries / month' },
                { text: 'Chat history (7 days)' },
                { text: 'Schema explorer' },
                { text: 'Team collaboration', muted: true },
                { text: 'Priority support', muted: true },
              ]}
              cta="Get started free"
              delay={0}
              onCTA={() => navigate('/sign-up')}
            />
            <PricingCard
              plan="Pro"
              price="$29"
              period="mo"
              features={[
                { text: '10 database connections' },
                { text: 'Unlimited queries' },
                { text: 'Full query history' },
                { text: 'Analytics dashboard' },
                { text: 'Bring your own API key' },
                { text: 'Priority support', muted: true },
              ]}
              cta="Start Pro trial"
              highlight
              delay={100}
              onCTA={() => navigate('/sign-up')}
            />
            <PricingCard
              plan="Enterprise"
              price="Custom"
              features={[
                { text: 'Unlimited connections' },
                { text: 'Unlimited queries' },
                { text: 'SSO / SAML' },
                { text: 'SOC 2 compliance docs' },
                { text: 'SLA guarantee' },
                { text: 'Dedicated support' },
              ]}
              cta="Contact Sales"
              delay={200}
              onCTA={() => {}}
            />
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          FINAL CTA
      ───────────────────────────────────────────────────────── */}
      <section className="py-28 px-6 relative overflow-hidden" style={{ background: '#101321' }}>
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] rounded-full" style={{ background: 'radial-gradient(ellipse, rgba(64,204,183,0.12) 0%, transparent 70%)', filter: 'blur(40px)' }} />
        </div>
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <Reveal>
            <div className="w-16 h-16 rounded-2xl mx-auto mb-8 flex items-center justify-center" style={{ background: 'rgba(64,204,183,0.12)', border: '1px solid rgba(64,204,183,0.3)' }}>
              <span className="material-symbols-outlined text-primary text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
            </div>
            <h2 className="font-display font-bold text-white mb-5" style={{ fontSize: 'clamp(2rem, 5vw, 3.25rem)', letterSpacing: '-0.03em' }}>
              Your data deserves better questions
            </h2>
            <p className="text-muted-foreground leading-relaxed mb-10 max-w-xl mx-auto" style={{ fontSize: '1.1rem' }}>
              Join thousands of analysts and engineers who are already getting faster, smarter insights with QueryTalk AI.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => navigate('/sign-up')}
                id="cta-final-signup-btn"
                className="px-10 py-4 rounded-xl text-base font-bold font-display flex items-center gap-2 transition-all"
                style={{ background: '#40CCB7', color: '#002E28' }}
                onMouseEnter={e => { e.currentTarget.style.opacity = '0.88'; e.currentTarget.style.boxShadow = '0 0 40px rgba(64,204,183,0.4)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'translateY(0)'; }}
              >
                Start for Free
                <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
              </button>
              <button
                onClick={() => navigate('/sign-in')}
                className="px-8 py-4 rounded-xl text-base font-semibold transition-all"
                style={{ background: 'transparent', border: '1px solid #2A2D3D', color: '#9CA3AF' }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(64,204,183,0.35)'; e.currentTarget.style.color = '#fff'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = '#2A2D3D'; e.currentTarget.style.color = '#9CA3AF'; }}
              >
                Sign In
              </button>
            </div>
            <p className="text-xs font-mono text-muted-foreground/50 mt-6">
              No credit card required · Setup in 2 minutes · Cancel anytime
            </p>
          </Reveal>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────
          FOOTER
      ───────────────────────────────────────────────────────── */}
      <footer className="py-10 px-6" style={{ background: '#0C0E1A', borderTop: '1px solid #2A2D3D' }}>
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'rgba(64,204,183,0.12)', border: '1px solid rgba(64,204,183,0.25)' }}>
              <span className="material-symbols-outlined text-primary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>neurology</span>
            </div>
            <span className="font-display font-bold text-white text-sm">QueryTalk AI</span>
          </div>
          <p className="text-xs font-mono text-muted-foreground/60 text-center">
            © {new Date().getFullYear()} QueryTalk AI. All rights reserved. · End-to-end encrypted.
          </p>
          <div className="flex items-center gap-4">
            {['Privacy', 'Terms', 'Security'].map(link => (
              <a key={link} href="#" className="text-xs text-muted-foreground hover:text-white transition-colors">{link}</a>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
