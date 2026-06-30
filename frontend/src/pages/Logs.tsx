import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { ShieldAlert, CheckCircle, Search } from "lucide-react";

export const LogsPage: React.FC = () => {
  const [limit, setLimit] = useState(25);
  const [providerFilter, setProviderFilter] = useState("");
  
  // Fetch logs
  const { data: logs, isLoading } = useQuery({
    queryKey: ["logs", limit, providerFilter],
    queryFn: async () => {
      const params: any = { limit };
      if (providerFilter) {
        params.provider = providerFilter;
      }
      const res = await apiClient.get("/api/v1/logs", { params });
      return res.data;
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Request Logs
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Browse and debug completions gateway request histories.
          </p>
        </div>
      </div>

      {/* Filter bar */}
      <div className="p-4 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm flex items-center justify-between gap-4">
        <div className="flex items-center space-x-2 w-full max-w-md bg-slate-50 dark:bg-slate-900 px-3 py-2 rounded-xl border border-slate-100 dark:border-slate-800">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={providerFilter}
            onChange={(e) => setProviderFilter(e.target.value)}
            placeholder="Filter by provider..."
            className="bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-500 w-full focus:outline-none"
          />
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs font-semibold text-slate-400 uppercase">Limit:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-transparent text-xs text-slate-700 dark:text-slate-300 focus:outline-none"
          >
            <option value={10}>10 items</option>
            <option value={25}>25 items</option>
            <option value={50}>50 items</option>
            <option value={100}>100 items</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-slate-500">Loading activity history...</div>
      ) : (
        <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/80">
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400">Timestamp</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400">Provider</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400">Model</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-center">Status</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Tokens</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Latency</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
              {logs?.map((log: any) => (
                <tr key={log.id} className="hover:bg-slate-50/20 dark:hover:bg-slate-800/20 transition-colors">
                  <td className="p-4 text-xs text-slate-400 font-mono font-medium">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="p-4 font-semibold text-slate-900 dark:text-white text-sm">
                    {log.provider_name}
                  </td>
                  <td className="p-4 text-xs text-slate-500 dark:text-slate-400 font-mono">
                    {log.model_name || "-"}
                  </td>
                  <td className="p-4 text-center">
                    <span
                      className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                        log.success
                          ? "bg-emerald-500/10 text-emerald-500"
                          : "bg-rose-500/10 text-rose-500"
                      }`}
                    >
                      {log.success ? (
                        <CheckCircle className="w-3 h-3" />
                      ) : (
                        <ShieldAlert className="w-3 h-3" />
                      )}
                      <span>{log.success ? "Success" : "Failed"}</span>
                    </span>
                  </td>
                  <td className="p-4 text-right text-xs text-slate-500 font-mono">
                    {log.total_tokens ? log.total_tokens.toLocaleString() : 0}
                  </td>
                  <td className="p-4 text-right text-xs text-slate-500 font-semibold font-mono">
                    {log.duration_ms ? `${log.duration_ms.toFixed(0)} ms` : "-"}
                  </td>
                  <td className="p-4 text-right text-xs font-bold font-mono text-slate-700 dark:text-slate-300">
                    {log.cost ? `$${log.cost.toFixed(5)}` : "$0.00"}
                  </td>
                </tr>
              ))}
              {(!logs || logs.length === 0) && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400 text-sm">
                    No matching activity logs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
