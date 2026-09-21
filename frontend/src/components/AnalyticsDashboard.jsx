import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@clerk/react';
import useStore from '../store';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter, ZAxis, PieChart, Pie, Cell } from 'recharts';



const formatNumber = (num) => {
  if (num === null || num === undefined) return '0';
  const val = parseFloat(num);
  if (isNaN(val)) return num;
  if (val >= 1e12) return (val / 1e12).toFixed(1) + 'T';
  if (val >= 1e9) return (val / 1e9).toFixed(1) + 'B';
  if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
  if (val >= 1e3) return (val / 1e3).toFixed(1) + 'k';
  return val.toFixed(1).endsWith('.0') ? val.toFixed(0) : val.toFixed(1);
};

const formatYAxis = (v) => {
  if (v === null || v === undefined) return '0';
  const val = parseFloat(v);
  if (isNaN(val)) return v;
  if (val >= 1e12) return `${(val / 1e12).toFixed(1)}T`;
  if (val >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  if (val >= 1e3) return `${(val / 1e3).toFixed(1)}k`;
  return val.toFixed(1).endsWith('.0') ? val.toFixed(0) : val.toFixed(1);
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-surface-container-high border border-white/10 p-3 rounded-lg shadow-xl" style={{ background: '#1C1E2D' }}>
        <p className="text-on-surface font-medium text-white mb-1.5">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-sm font-mono" style={{ color: entry.color || '#40CCB7' }}>
            {entry.name}: {typeof entry.value === 'number' ? formatNumber(entry.value) : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function AnalyticsDashboard() {
  const { getToken } = useAuth();
  const { dbStatus } = useStore();
  const [loading, setLoading] = useState(true);
  const [fallback, setFallback] = useState(false);
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (dbStatus !== 'connected') {
        setLoading(false);
        return;
      }
      try {
        const clerkToken = await getToken();
        const res = await axios.get('/api/db/analytics', { headers: { Authorization: `Bearer ${clerkToken}` }});
        if (res.data.fallback) {
          setFallback(true);
          // Load default mock data
          setData({
            kpis: { totalRevenue: 2400000, growthPct: 28.4, activeCustomers: 14290, monthlySales: 8402 },
            growthData: [
              { name: 'Jan', current: 4000, projected: 2400 },
              { name: 'Feb', current: 4500, projected: 2800 },
              { name: 'Mar', current: 5200, projected: 3100 },
              { name: 'Apr', current: 6100, projected: 3500 },
              { name: 'May', current: 6800, projected: 3900 },
              { name: 'Jun', current: 7500, projected: 4200 }
            ],
            marketShareData: [
              { name: 'North America', value: 62, color: '#40CCB7' },
              { name: 'Europe', value: 25, color: '#df7412' },
              { name: 'APAC', value: 13, color: '#00a2e6' }
            ],
            revenueRegionData: [
              { name: 'NA', value: 120 }, { name: 'EU', value: 80 }, { name: 'APAC', value: 150 }
            ],
            customerSegmentsData: [
              { x: 10, y: 30, z: 200, group: 1 }, { x: 40, y: 80, z: 300, group: 2 }, { x: 70, y: 15, z: 400, group: 3 }
            ]
          });
        } else {
          setFallback(false);
          setData(res.data);
        }
      } catch (err) {
        console.error("Failed to fetch analytics", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [getToken, dbStatus]);

  if (loading) {
    return <div className="w-full h-full flex items-center justify-center text-primary animate-pulse">Loading Live Analytics...</div>;
  }

  if (!data) {
    return (
        <div className="w-full h-full flex flex-col items-center justify-center text-on-surface-variant">
            <span className="material-symbols-outlined text-[64px] opacity-50 mb-4">link_off</span>
            <p>Connect a database to view analytics.</p>
        </div>
    );
  }

  const { kpis, growthData, marketShareData, revenueRegionData, customerSegmentsData } = data;

  // Process Market Share counts dynamically into percentages
  const totalMarketShare = marketShareData ? marketShareData.reduce((sum, item) => sum + (parseFloat(item.value) || 0), 0) : 0;
  
  const formattedMarketShare = marketShareData ? marketShareData.map(item => {
    const val = parseFloat(item.value) || 0;
    const pct = totalMarketShare > 0 ? (val / totalMarketShare) * 100 : 0;
    return {
      ...item,
      value: pct,
      rawValue: val
    };
  }) : [];

  const largestSegment = formattedMarketShare.length > 0 
    ? formattedMarketShare.reduce((prev, current) => (prev.value > current.value) ? prev : current)
    : null;

  // Resolve unique groups dynamically for Scatter chart
  const uniqueGroups = Array.from(new Set(customerSegmentsData ? customerSegmentsData.map(d => d.group) : []));
  const groupColors = ['#40CCB7', '#df7412', '#00a2e6', '#93000a', '#ffb786', '#e600a2'];

  return (
    <div className="w-full h-full flex flex-col gap-6 animate-fade-in pb-12">
      {/* Header Area */}
      
      {fallback && (
        <div className="bg-tertiary-container/20 border border-tertiary-container text-on-surface px-4 py-3 rounded-lg flex items-center gap-3">
            <span className="material-symbols-outlined text-tertiary-container">info</span>
            <p className="text-sm">Showing sample analytics. Connect to the standard demo schema for live data.</p>
        </div>
      )}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-headline-lg font-bold text-on-surface tracking-tight">Performance Dashboard</h2>
          <p className="font-body-lg text-on-surface-variant mt-1">Real-time telemetry and predictive insights.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 bg-surface-container-high hover:bg-surface-variant text-on-surface-variant hover:text-on-surface px-4 py-2 rounded-lg border border-white/5 transition-colors">
            <span className="material-symbols-outlined text-[18px]">calendar_month</span>
            <span className="font-medium text-sm">Last 30 Days</span>
          </button>
          <button className="flex items-center gap-2 bg-surface-container-high hover:bg-surface-variant text-on-surface-variant hover:text-on-surface px-4 py-2 rounded-lg border border-white/5 transition-colors">
            <span className="material-symbols-outlined text-[18px]">filter_list</span>
            <span className="font-medium text-sm">Filter</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Revenue */}
        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col gap-4">
          <div className="flex justify-between items-start">
            <h3 className="font-label-mono text-xs font-bold text-on-surface-variant tracking-wider uppercase">Total Revenue</h3>
            <span className="material-symbols-outlined text-primary/70">payments</span>
          </div>
          <div>
            <h4 className="font-display text-3xl font-bold text-on-surface">${formatNumber(kpis.totalRevenue)}</h4>
            <div className="flex items-center gap-1 mt-1 text-secondary">
              <span className="material-symbols-outlined text-[16px]">trending_up</span>
              <span className="text-sm font-medium">{kpis.growthPct > 0 ? '+' : ''}{kpis.growthPct.toFixed(1)}% vs last month</span>
            </div>
          </div>
        </div>

        {/* Growth % */}
        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col gap-4">
          <div className="flex justify-between items-start">
            <h3 className="font-label-mono text-xs font-bold text-on-surface-variant tracking-wider uppercase">Growth %</h3>
            <span className="material-symbols-outlined text-tertiary-container/70">show_chart</span>
          </div>
          <div>
            <h4 className="font-display text-3xl font-bold text-on-surface">{kpis.growthPct.toFixed(1)}%</h4>
            <div className="flex items-center gap-1 mt-1 text-tertiary-container">
              <span className="material-symbols-outlined text-[16px]">{kpis.growthPct >= 0 ? 'trending_up' : 'trending_down'}</span>
              <span className="text-sm font-medium">{kpis.growthPct >= 0 ? 'Upward trajectory' : 'Downward trend'}</span>
            </div>
          </div>
        </div>

        {/* Active Customers */}
        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col gap-4">
          <div className="flex justify-between items-start">
            <h3 className="font-label-mono text-xs font-bold text-on-surface-variant tracking-wider uppercase">Active Customers</h3>
            <span className="material-symbols-outlined text-primary-container/70">groups</span>
          </div>
          <div>
            <h4 className="font-display text-3xl font-bold text-on-surface">{formatNumber(kpis.activeCustomers)}</h4>
            <div className="flex items-center gap-1 mt-1 text-on-surface-variant">
              <span className="material-symbols-outlined text-[16px]">horizontal_rule</span>
              <span className="text-sm font-medium">Steady state</span>
            </div>
          </div>
        </div>

        {/* Monthly Sales */}
        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col gap-4">
          <div className="flex justify-between items-start">
            <h3 className="font-label-mono text-xs font-bold text-on-surface-variant tracking-wider uppercase">Monthly Sales</h3>
            <span className="material-symbols-outlined text-error/70">point_of_sale</span>
          </div>
          <div>
            <h4 className="font-display text-3xl font-bold text-on-surface">{formatNumber(kpis.monthlySales)}</h4>
            <div className="flex items-center gap-1 mt-1 text-error">
              <span className="material-symbols-outlined text-[16px]">trending_up</span>
              <span className="text-sm font-medium">Live telemetry</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Growth Trends - Area Chart */}
        <div className="lg:col-span-2 bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col h-[400px]">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-display text-xl font-medium text-on-surface">Growth Trends</h3>
            <button className="text-on-surface-variant hover:text-on-surface"><span className="material-symbols-outlined">more_horiz</span></button>
          </div>
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={growthData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCurrent" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#40CCB7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#40CCB7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#8c909f" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#8c909f" fontSize={12} tickLine={false} axisLine={false} tickFormatter={formatYAxis} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="projected" stroke="#8c909f" strokeDasharray="5 5" fill="none" strokeWidth={2} name="Projected" />
                <Area type="monotone" dataKey="current" stroke="#40CCB7" fillOpacity={1} fill="url(#colorCurrent)" strokeWidth={3} name="Current" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Market Share - Pie/Donut Chart */}
        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col h-[400px]">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-display text-xl font-medium text-on-surface">Market Share</h3>
            <button className="text-on-surface-variant hover:text-on-surface"><span className="material-symbols-outlined">more_horiz</span></button>
          </div>
          <div className="flex-1 flex flex-col items-center justify-center relative">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={formattedMarketShare}
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {formattedMarketShare.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || groupColors[index % groupColors.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none mt-[-20px]">
              <div className="text-center px-4 w-full">
                <span className="block font-display text-3xl font-bold text-on-surface truncate">
                  {largestSegment ? `${largestSegment.value.toFixed(0)}%` : '0%'}
                </span>
                <span className="text-xs text-on-surface-variant font-medium truncate max-w-[120px] block mx-auto">
                  {largestSegment ? largestSegment.name : 'No Segment'}
                </span>
              </div>
            </div>
          </div>
          <div className="mt-auto flex flex-col gap-2 pt-4 max-h-[120px] overflow-y-auto pr-1">
            {formattedMarketShare.map((item, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: item.color || groupColors[i % groupColors.length] }}></span>
                  <span className="text-sm text-on-surface-variant truncate max-w-[150px]">{item.name}</span>
                </div>
                <span className="text-sm font-medium text-on-surface shrink-0">{item.value.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Secondary Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue by Region - Bar Chart */}
        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col h-[350px]">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-display text-xl font-medium text-on-surface">Revenue by Region</h3>
            <button className="text-on-surface-variant hover:text-on-surface"><span className="material-symbols-outlined">more_horiz</span></button>
          </div>
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenueRegionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#8c909f" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#8c909f" fontSize={12} tickLine={false} axisLine={false} tickFormatter={formatYAxis} />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} content={<CustomTooltip />} />
                <Bar dataKey="value" fill="#40CCB7" radius={[4, 4, 0, 0]} name="Value" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Customer Segments - Scatter Chart */}
        <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl border border-white/5 p-5 flex flex-col h-[350px]">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-4">
                <h3 className="font-display text-xl font-medium text-on-surface">Customer Segments</h3>
                <span className="px-2 py-1 rounded bg-surface-container-highest text-on-surface-variant text-[10px] font-label-mono tracking-wider">Clustering: K-Means</span>
            </div>
            <button className="text-on-surface-variant hover:text-on-surface"><span className="material-symbols-outlined">more_horiz</span></button>
          </div>
          <div className="flex-1 w-full min-h-0 relative">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" dataKey="x" stroke="#8c909f" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis type="number" dataKey="y" stroke="#8c909f" fontSize={12} tickLine={false} axisLine={false} />
                <ZAxis type="number" dataKey="z" range={[50, 400]} />
                <Tooltip cursor={{strokeDasharray: '3 3'}} content={<CustomTooltip />} />
                {uniqueGroups.map((grp, idx) => (
                  <Scatter 
                    key={grp}
                    name={String(grp)} 
                    data={customerSegmentsData.filter(d => d.group === grp)} 
                    fill={groupColors[idx % groupColors.length]} 
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
            <div className="absolute left-0 bottom-4 origin-bottom-left -rotate-90 transform text-xs text-on-surface-variant">
              Metrics Ratio
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
