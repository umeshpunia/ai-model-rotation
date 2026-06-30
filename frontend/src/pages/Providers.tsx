import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { Plus, Edit2, Trash2, ShieldAlert, CheckCircle, RefreshCw } from "lucide-react";
import { notifySuccess, notifyError, confirmAction } from "../utils/alerts";

export const ProvidersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedProvider, setSelectedProvider] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Form State
  const [name, setName] = useState("");
  const [apiFormat, setApiFormat] = useState("openai");
  const [baseUrl, setBaseUrl] = useState("");
  const [isActive, setIsActive] = useState(true);

  // Fetch providers
  const { data: providers, isLoading } = useQuery({
    queryKey: ["providers"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/providers");
      return res.data;
    },
  });

  // Create or Update Mutation
  const saveMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (selectedProvider) {
        await apiClient.put(`/api/v1/providers/${selectedProvider.id}`, payload);
      } else {
        await apiClient.post("/api/v1/providers", payload);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
      closeModal();
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/api/v1/providers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] });
    },
  });

  // Test Connection Mutation
  const testMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await apiClient.post(`/api/v1/providers/${id}/test`);
      return res.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        notifySuccess(data.message || "Provider connection succeeded!");
      } else {
        notifyError(data.message || "Provider connection failed!");
      }
    },
    onError: () => {
      notifyError("Failed to reach provider. Verify credentials or base URL.");
    },
  });

  const openAddModal = () => {
    setSelectedProvider(null);
    setName("");
    setApiFormat("openai");
    setBaseUrl("");
    setIsActive(true);
    setIsModalOpen(true);
  };

  const openEditModal = (provider: any) => {
    setSelectedProvider(provider);
    setName(provider.name);
    setApiFormat(provider.api_format);
    setBaseUrl(provider.base_url || "");
    setIsActive(provider.is_active);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedProvider(null);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate({
      name,
      api_format: apiFormat,
      base_url: baseUrl || null,
      is_active: isActive,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Providers
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Configure backend LLM engine provider integrations.
          </p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-500 text-white font-medium text-sm px-4 py-2.5 rounded-xl shadow-lg shadow-violet-500/10 active:scale-95 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Add Provider</span>
        </button>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-slate-500">Loading configurations...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {providers?.map((provider: any) => (
            <div
              key={provider.id}
              className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between"
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-slate-900 dark:text-white text-lg">
                      {provider.name}
                    </h3>
                    <span className="inline-flex px-2 py-0.5 rounded-md text-[10px] uppercase font-bold tracking-wider bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                      {provider.api_format}
                    </span>
                  </div>
                  <span
                    className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                      provider.is_active
                        ? "bg-emerald-500/10 text-emerald-500"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-400"
                    }`}
                  >
                    {provider.is_active ? <CheckCircle className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
                    <span>{provider.is_active ? "Active" : "Disabled"}</span>
                  </span>
                </div>

                <div className="text-xs text-slate-500 dark:text-slate-400 mt-4 break-all font-mono">
                  Base URL: {provider.base_url || "Default (Plugin configuration)"}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 mt-6 pt-4 border-t border-slate-100 dark:border-slate-800/80">
                <button
                  onClick={() => testMutation.mutate(provider.id)}
                  disabled={testMutation.isPending}
                  className="flex-1 py-2 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors flex items-center justify-center space-x-1"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${testMutation.isPending ? "animate-spin" : ""}`} />
                  <span>Test Connection</span>
                </button>
                <button
                  onClick={() => openEditModal(provider)}
                  className="p-2 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
                  title="Edit config"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={async () => {
                    const confirmed = await confirmAction({
                      title: "Delete Provider",
                      text: "Are you sure you want to delete this provider? This action is permanent.",
                      confirmButtonText: "Delete",
                      cancelButtonText: "Cancel"
                    });
                    if (confirmed) {
                      deleteMutation.mutate(provider.id);
                    }
                  }}
                  className="p-2 text-xs font-semibold rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 transition-colors"
                  title="Delete provider"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
              {selectedProvider ? "Edit Provider" : "Add Provider"}
            </h3>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Gemini Provider"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">API Format</label>
                <select
                  value={apiFormat}
                  onChange={(e) => setApiFormat(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all text-sm"
                >
                  <option value="openai" className="dark:bg-slate-900">OpenAI compatible</option>
                  <option value="anthropic" className="dark:bg-slate-900">Anthropic</option>
                  <option value="gemini" className="dark:bg-slate-900">Google Gemini</option>
                  <option value="ollama" className="dark:bg-slate-900">Ollama</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Base URL (Optional)</label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="e.g. https://api.openai.com/v1"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all text-sm"
                />
              </div>

              <div className="flex items-center space-x-3 pt-2">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="w-4 h-4 rounded text-violet-600 border-slate-300 focus:ring-violet-500"
                />
                <label htmlFor="isActive" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Enable Provider immediately
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
