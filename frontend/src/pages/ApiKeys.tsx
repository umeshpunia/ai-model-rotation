import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { Plus, Edit2, Trash2, Eye, EyeOff, ShieldAlert, CheckCircle, RefreshCw, Key } from "lucide-react";
import { notifySuccess, notifyError, confirmAction } from "../utils/alerts";

export const ApiKeysPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedKey, setSelectedKey] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Record<number, boolean>>({});

  // Form State
  const [providerId, setProviderId] = useState<number>(0);
  const [secretKey, setSecretKey] = useState("");
  const [priority, setPriority] = useState(1);
  const [isActive, setIsActive] = useState(true);

  // Fetch providers (for selection)
  const { data: providers } = useQuery({
    queryKey: ["providers"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/providers");
      return res.data;
    },
  });

  // Fetch API Keys
  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["apiKeys"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/keys");
      return res.data;
    },
  });

  // Save Mutation
  const saveMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (selectedKey) {
        await apiClient.put(`/api/v1/keys/${selectedKey.id}`, payload);
      } else {
        await apiClient.post("/api/v1/keys", payload);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
      closeModal();
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/keys/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
  });

  // Test Key Mutation
  const testMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await apiClient.post(`/api/v1/keys/${id}/test`);
      return res.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        notifySuccess(data.message || "Key test connection succeeded!");
      } else {
        notifyError(data.message || "Key test connection failed!");
      }
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
  });

  // Rotate Key Mutation
  const rotateMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await apiClient.post(`/api/v1/keys/${id}/rotate`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys"] });
    },
  });

  const toggleVisibility = (id: number) => {
    setVisibleKeys((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const openAddModal = () => {
    setSelectedKey(null);
    setProviderId(providers?.[0]?.id ?? 0);
    setSecretKey("");
    setPriority(1);
    setIsActive(true);
    setIsModalOpen(true);
  };

  const openEditModal = (key: any) => {
    setSelectedKey(key);
    setProviderId(key.provider_id);
    setSecretKey(""); // Don't pre-populate the secret password value
    setPriority(key.priority);
    setIsActive(key.is_active);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedKey(null);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: any = {
      provider_id: Number(providerId),
      priority: Number(priority),
      is_active: isActive,
    };
    if (secretKey) {
      payload.secret_key = secretKey;
    }
    saveMutation.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            API Keys
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Store and rotate secrets, monitor rates limits, failure triggers, and request latencies.
          </p>
        </div>
        <button
          onClick={openAddModal}
          disabled={!providers || providers.length === 0}
          className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-500 text-white font-medium text-sm px-4 py-2.5 rounded-xl shadow-lg shadow-violet-500/10 active:scale-95 transition-all disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          <span>Add API Key</span>
        </button>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-slate-500">Loading configurations...</div>
      ) : (
        <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/80">
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400">Provider</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400">Key Hash</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400">Status</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-center">Priority</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Failures</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Latency</th>
                <th className="p-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
              {apiKeys?.map((apiKey: any) => {
                const provider = providers?.find((p: any) => p.id === apiKey.provider_id);
                return (
                  <tr key={apiKey.id} className="hover:bg-slate-50/20 dark:hover:bg-slate-800/20 transition-colors">
                    <td className="p-4 font-semibold text-slate-900 dark:text-white text-sm">
                      {provider?.name || `Provider ID: ${apiKey.provider_id}`}
                    </td>
                    <td className="p-4 font-mono text-xs text-slate-500 dark:text-slate-400">
                      <div className="flex items-center space-x-2">
                        <span>
                          {visibleKeys[apiKey.id]
                            ? apiKey.secret_key || "••••••••••••••••"
                            : "••••••••" + apiKey.secret_key_masked}
                        </span>
                        <button
                          onClick={() => toggleVisibility(apiKey.id)}
                          className="text-slate-400 hover:text-slate-200"
                        >
                          {visibleKeys[apiKey.id] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </td>
                    <td className="p-4 text-xs font-semibold">
                      <span
                        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full ${
                          apiKey.status === "healthy"
                            ? "bg-emerald-500/10 text-emerald-500"
                            : apiKey.status === "cooldown"
                            ? "bg-amber-500/10 text-amber-500"
                            : "bg-rose-500/10 text-rose-500"
                        }`}
                      >
                        {apiKey.status === "healthy" ? (
                          <CheckCircle className="w-3.5 h-3.5" />
                        ) : (
                          <ShieldAlert className="w-3.5 h-3.5" />
                        )}
                        <span className="capitalize">{apiKey.status}</span>
                      </span>
                    </td>
                    <td className="p-4 text-center text-sm font-semibold text-slate-700 dark:text-slate-300">
                      {apiKey.priority}
                    </td>
                    <td className="p-4 text-right text-xs text-slate-500 font-medium">
                      {apiKey.failure_count || 0}
                    </td>
                    <td className="p-4 text-right text-xs text-slate-500 font-semibold font-mono">
                      {apiKey.avg_latency_ms ? `${Math.round(apiKey.avg_latency_ms)} ms` : "-"}
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => testMutation.mutate(apiKey.id)}
                          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors"
                          title="Test key connection"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => rotateMutation.mutate(apiKey.id)}
                          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors"
                          title="Trigger fallback cooldown"
                        >
                          <Key className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => openEditModal(apiKey)}
                          className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={async () => {
                            const confirmed = await confirmAction({
                              title: "Delete API Key",
                              text: "Are you sure you want to delete this API Key? This action is permanent.",
                              confirmButtonText: "Delete",
                              cancelButtonText: "Cancel"
                            });
                            if (confirmed) {
                              deleteMutation.mutate(apiKey.id);
                            }
                          }}
                          className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
              {selectedKey ? "Edit API Key" : "Add API Key"}
            </h3>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Provider Plugin</label>
                <select
                  disabled={!!selectedKey}
                  value={providerId}
                  onChange={(e) => setProviderId(Number(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all text-sm"
                >
                  {providers?.map((p: any) => (
                    <option key={p.id} value={p.id} className="dark:bg-slate-900">
                      {p.name} ({p.api_format})
                    </option>
                  ))}
                </select>
              </div>

              {!selectedKey && (
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-500">Secret Token/Key Value</label>
                  <input
                    type="password"
                    required
                    value={secretKey}
                    onChange={(e) => setSecretKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all text-sm"
                  />
                </div>
              )}

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Priority Weight (1 = highest)</label>
                <input
                  type="number"
                  min={1}
                  required
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all text-sm"
                />
              </div>

              <div className="flex items-center space-x-3 pt-2">
                <input
                  type="checkbox"
                  id="keyIsActive"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-4 h-4 rounded text-violet-600 border-slate-300 focus:ring-violet-500"
                />
                <label htmlFor="keyIsActive" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Enable API Key immediately
                </label>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-xs font-semibold border border-slate-200 dark:border-slate-800 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white rounded-xl shadow-lg shadow-violet-500/10 active:scale-95 transition-all"
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
