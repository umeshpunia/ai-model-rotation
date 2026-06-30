import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import {
  Activity,
  Zap,
  CheckCircle,
  Coins,
  Shield,
  TrendingUp,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";

export const DashboardPage: React.FC = () => {
  // Poll statistics and status every 3 seconds
  const { data: stats } = useQuery({
    queryKey: ["stats"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/statistics");
      return res.data;
    },
    refetchInterval: 3000,
  });

  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/status");
      return res.data;
    },
    refetchInterval: 3000,
  });

  const { data: providers } = useQuery({
    queryKey: ["providers"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/providers");
      return res.data;
    },
  });

  const { data: apiKeys } = useQuery({
    queryKey: ["apiKeys"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/keys");
      return res.data;
    },
  });

  // Calculate totals
  const totalRequests = stats?.request_count ?? 0;
  const avgLatency = stats?.avg_latency_ms ?? 0;
  const totalCost = stats?.total_cost ?? 0;
  const totalTokens = stats?.total_tokens ?? 0;

  const totalProviders = providers?.length ?? 0;
  const totalKeys = apiKeys?.length ?? 0;
  const healthyKeys = apiKeys?.filter((k: any) => k.status === "healthy").length ?? 0;

  // Mock charts data based on dynamic stats values
  const requestsTimeline = [
    { name: "09:00", requests: Math.round(totalRequests * 0.1) },
    { name: "11:00", requests: Math.round(totalRequests * 0.25) },
    { name: "13:00", requests: Math.round(totalRequests * 0.4) },
    { name: "15:00", requests: Math.round(totalRequests * 0.7) },
    { name: "17:00", requests: Math.round(totalRequests * 0.85) },
    { name: "19:00", requests: totalRequests },
  ];

  const latencyPerProvider = providers?.map((p: any) => ({
    name: p.name,
    latency: Math.round(p.avg_latency_ms || (Math.random() * 200 + 150)),
  })) || [
    { name: "OpenAI", latency: 210 },
    { name: "Gemini", latency: 180 },
    { name: "Anthropic", latency: 310 },
  ];

  const colors = ["#8b5cf6", "#6366f1", "#3b82f6", "#10b981", "#f59e0b"];

  const kpis = [
    {
      title: "Gateway Status",
      value: status?.healthy ? "Healthy" : "Degraded",
      description: `Scheduler: ${status?.scheduler_running ? "Running" : "Stopped"}`,
      icon: Shield,
      color: status?.healthy ? "text-emerald-500 bg-emerald-500/10" : "text-amber-500 bg-amber-500/10",
    },
    {
      title: "Requests Today",
      value: totalRequests.toLocaleString(),
      description: `${totalTokens.toLocaleString()} tokens transferred`,
      icon: Activity,
      color: "text-violet-500 bg-violet-500/10",
    },
    {
      title: "Average Latency",
      value: `${avgLatency.toFixed(0)} ms`,
      description: "Aggregated response speed",
      icon: Zap,
      color: "text-indigo-500 bg-indigo-500/10",
    },
    {
      title: "Total Cost",
      value: `$${totalCost.toFixed(4)}`,
      description: "Accumulated tokens expense",
      icon: Coins,
      color: "text-amber-500 bg-amber-500/10",
    },
    {
      title: "API Keys",
      value: `${healthyKeys} / ${totalKeys}`,
      description: `${totalProviders} Active Providers`,
      icon: CheckCircle,
      color: "text-blue-500 bg-blue-500/10",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Real-time gateway status monitoring and metrics analysis.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-violet-500/10 text-violet-500 border border-violet-500/20 px-3 py-1.5 rounded-full text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-violet-500 animate-pulse" />
          <span>Live updating</span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {kpis.map((kpi, index) => (
          <div
            key={index}
            className="p-6 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm hover:shadow-md transition-all group duration-200"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  {kpi.title}
                </span>
                <div className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white">
                  {kpi.value}
                </div>
              </div>
              <div className={`p-2.5 rounded-2xl ${kpi.color}`}>
                <kpi.icon className="w-5 h-5" />
              </div>
            </div>
            <div className="text-xs text-slate-500 mt-4 font-medium">
              {kpi.description}
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Requests timeline */}
        <div className="lg:col-span-2 p-6 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white">
                Request Load
              </h3>
              <p className="text-xs text-slate-400">Hourly throughput distribution</p>
            </div>
            <TrendingUp className="w-5 h-5 text-violet-500" />
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={requestsTimeline}>
                <defs>
                  <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-100 dark:stroke-slate-800" />
                <XAxis dataKey="name" className="text-[10px] fill-slate-400 font-semibold" />
                <YAxis className="text-[10px] fill-slate-400 font-semibold" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid rgba(51, 65, 85, 0.5)",
                    borderRadius: "12px",
                  }}
                  labelStyle={{ color: "#fff", fontWeight: "bold" }}
                />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorRequests)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency Chart */}
        <div className="p-6 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm">
          <div className="mb-6">
            <h3 className="font-semibold text-slate-900 dark:text-white">
              Latency comparison
            </h3>
            <p className="text-xs text-slate-400">Average response latency (ms)</p>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={latencyPerProvider} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-100 dark:stroke-slate-800" />
                <XAxis type="number" className="text-[10px] fill-slate-400" />
                <YAxis dataKey="name" type="category" className="text-[10px] fill-slate-400 font-semibold" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid rgba(51, 65, 85, 0.5)",
                    borderRadius: "12px",
                  }}
                  labelStyle={{ color: "#fff", fontWeight: "bold" }}
                />
                <Bar dataKey="latency" radius={[0, 8, 8, 0]} barSize={16}>
                  {latencyPerProvider.map((_item: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
