import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { RefreshCw, Download, Upload, Trash2, ArrowUpCircle } from "lucide-react";

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [profile, setProfile] = useState("default");
  
  // Settings Import State
  const [importJson, setImportJson] = useState("");
  const [overwrite, setOverwrite] = useState(true);

  // Fetch settings for active profile
  const { data: settingsList, isLoading: loadingSettings } = useQuery({
    queryKey: ["settings", profile],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/settings", { params: { profile } });
      return res.data;
    },
  });

  // Fetch backups list
  const { data: backups, isLoading: loadingBackups } = useQuery({
    queryKey: ["backups"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/backups");
      return res.data;
    },
  });

  // Create Backup Mutation
  const createBackupMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post("/api/v1/backups");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backups"] });
      alert("Backup snapshot created successfully.");
    },
  });

  // Restore Backup Mutation
  const restoreBackupMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.post(`/api/v1/backups/${id}/restore`);
    },
    onSuccess: () => {
      alert("Database snapshot restored successfully.");
      window.location.reload(); // Reload context since active DB state re-initialized
    },
    onError: () => {
      alert("Restore failed. Verify engine health.");
    },
  });

  // Delete Backup Mutation
  const deleteBackupMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/backups/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
  });

  // Export JSON Configuration
  const handleExport = async () => {
    try {
      const res = await apiClient.get("/api/v1/settings/export", { params: { profile } });
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `aigateway_profile_${profile}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Export failed.");
    }
  };

  // Import JSON Configuration
  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = JSON.parse(importJson);
      await apiClient.post("/api/v1/settings/import", {
        profile,
        overwrite,
        settings: payload.settings || payload,
      });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setImportJson("");
      alert("Configuration snapshot imported successfully.");
    } catch (err: any) {
      alert(err.message || "Invalid JSON configuration syntax.");
    }
  };

  // Claude Settings State
  const [claudeApiKey, setClaudeApiKey] = useState("");
  const [claudeBaseUrl, setClaudeBaseUrl] = useState("");
  const [claudeExists, setClaudeExists] = useState(false);

  // Fetch Claude settings
  const { data: claudeData } = useQuery({
    queryKey: ["claudeSettings"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/settings/claude");
      if (res.data) {
        setClaudeApiKey(res.data.apiKey || "");
        setClaudeBaseUrl(res.data.baseUrl || "");
        setClaudeExists(res.data.exists || false);
      }
      return res.data;
    },
  });

  // Update Claude Settings Mutation
  const updateClaudeMutation = useMutation({
    mutationFn: async (payload: { api_key: string; base_url: string }) => {
      await apiClient.post("/api/v1/settings/claude", payload);
    },
    onSuccess: () => {
      alert("Claude CLI settings updated and backed up successfully.");
      queryClient.invalidateQueries({ queryKey: ["claudeSettings"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to update Claude settings.");
    }
  });

  // Restore Claude Settings Mutation
  const restoreClaudeMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post("/api/v1/settings/claude/restore");
    },
    onSuccess: () => {
      alert("Claude settings.json restored successfully from settings.json.bak.");
      queryClient.invalidateQueries({ queryKey: ["claudeSettings"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Restore failed. Verify if backup file exists.");
    }
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          Settings & Backups
        </h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Adjust active configuration profiles, export snapshots, and manage database rolling backups.
        </p>
      </div>

      {/* Main Settings Panel Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Side: Profiles & Import/Export */}
        <div className="space-y-8">
          <div className="p-6 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-4">
              Active Environment Profile
            </h3>
            <div className="flex gap-2">
              {["default", "development", "production", "testing"].map((p) => (
                <button
                  key={p}
                  onClick={() => setProfile(p)}
                  className={`px-4 py-2 text-xs font-semibold rounded-xl capitalize transition-all duration-200 ${
                    profile === p
                      ? "bg-violet-600 text-white shadow-md shadow-violet-600/10"
                      : "border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            {loadingSettings ? (
              <div className="py-6 text-xs text-slate-500">Loading settings list...</div>
            ) : (
              <div className="mt-6 space-y-3 max-h-60 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/80">
                {settingsList?.map((s: any) => (
                  <div key={s.id} className="pt-3 flex justify-between text-xs">
                    <span className="font-medium text-slate-500 font-mono">{s.key}</span>
                    <span className="font-semibold text-slate-900 dark:text-white font-mono break-all pl-4 text-right">
                      {s.is_secret ? "••••••••" : s.value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-6 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
              Import & Export Snapshot
            </h3>
            <p className="text-xs text-slate-400 mb-4">Export current settings or import a backup JSON configuration snapshot.</p>
            <div className="flex space-x-2 mb-6">
              <button
                onClick={handleExport}
                className="flex items-center space-x-2 py-2 px-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export JSON</span>
              </button>
            </div>

            <form onSubmit={handleImport} className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800/80">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Import Configuration JSON</label>
                <textarea
                  value={importJson}
                  onChange={(e) => setImportJson(e.target.value)}
                  placeholder='{ "settings": [ ... ] }'
                  rows={4}
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white placeholder-slate-500 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all"
                />
              </div>
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="overwrite"
                  checked={overwrite}
                  onChange={(e) => setOverwrite(e.target.checked)}
                  className="w-4 h-4 rounded text-violet-600 border-slate-300 focus:ring-violet-500"
                />
                <label htmlFor="overwrite" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Overwrite conflicts (existing key configs)
                </label>
              </div>
              <button
                type="submit"
                className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs px-4 py-2.5 rounded-xl transition-colors shadow-lg shadow-violet-500/10"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Import Configuration</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Side: Backups Lifecycle & Claude CLI Configuration */}
        <div className="space-y-8">
          <div className="p-6 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm h-fit">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Database Snapshots
                </h3>
                <p className="text-xs text-slate-400 mt-1">Rolling SQLite database backups.</p>
              </div>
              <button
                onClick={() => createBackupMutation.mutate()}
                disabled={createBackupMutation.isPending}
                className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs px-4 py-2.5 rounded-xl shadow-lg shadow-violet-500/10 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${createBackupMutation.isPending ? "animate-spin" : ""}`} />
                <span>Create Snapshot</span>
              </button>
            </div>

            {loadingBackups ? (
              <div className="py-6 text-center text-slate-500 text-xs">Retrieving database backups...</div>
            ) : (
              <div className="space-y-4 max-h-[250px] overflow-y-auto">
                {backups?.map((backup: any) => (
                  <div
                    key={backup.id}
                    className="p-4 bg-slate-50 dark:bg-slate-900/80 rounded-2xl border border-slate-100 dark:border-slate-800/80 flex items-center justify-between"
                  >
                    <div className="space-y-1">
                      <div className="text-xs font-semibold text-slate-900 dark:text-white truncate max-w-[200px]">
                        {backup.filename}
                      </div>
                      <div className="text-[10px] text-slate-400 font-medium">
                        {new Date(backup.created_at).toLocaleString()} • {(backup.size_bytes / 1024).toFixed(1)} KB
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          if (confirm("Restore database? Current active transaction engine will reboot.")) {
                            restoreBackupMutation.mutate(backup.id);
                          }
                        }}
                        disabled={restoreBackupMutation.isPending}
                        className="flex items-center space-x-1.5 py-1.5 px-3 rounded-lg bg-emerald-500/15 text-emerald-500 hover:bg-emerald-500/20 text-xs font-semibold transition-colors"
                      >
                        <ArrowUpCircle className="w-3.5 h-3.5" />
                        <span>Restore</span>
                      </button>
                      <button
                        onClick={() => {
                          if (confirm("Delete this database backup snapshot?")) {
                            deleteBackupMutation.mutate(backup.id);
                          }
                        }}
                        className="p-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
                {(!backups || backups.length === 0) && (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    No database backup snapshots found.
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="p-6 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Claude CLI Configuration (~/.claude/settings.json)
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Manage connection keys, base URLs, and backups for your local Claude CLI.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Claude Base URL</label>
                <input
                  type="text"
                  value={claudeBaseUrl}
                  onChange={(e) => setClaudeBaseUrl(e.target.value)}
                  placeholder="https://capi.aerolink.lat/ or http://localhost:8080/v1"
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Claude API Key</label>
                <input
                  type="password"
                  value={claudeApiKey}
                  onChange={(e) => setClaudeApiKey(e.target.value)}
                  placeholder="aero_live_..."
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white placeholder-slate-500 text-xs focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => updateClaudeMutation.mutate({ api_key: claudeApiKey, base_url: claudeBaseUrl })}
                  disabled={updateClaudeMutation.isPending}
                  className="flex items-center space-x-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-semibold text-xs px-4 py-2.5 rounded-xl shadow-lg shadow-violet-500/10 transition-colors"
                >
                  <span>Update Claude Config</span>
                </button>
                
                <button
                  onClick={() => {
                    if (confirm("Are you sure you want to restore Claude settings from the backup file?")) {
                      restoreClaudeMutation.mutate();
                    }
                  }}
                  disabled={restoreClaudeMutation.isPending}
                  className="flex items-center space-x-1.5 py-2 px-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors"
                >
                  <span>Restore Claude Backup</span>
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
