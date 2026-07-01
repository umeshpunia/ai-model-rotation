import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { 
  Cpu, Wrench, Check, CheckCircle, Key, Sparkles, 
  ArrowRight, ArrowLeft, Search, Loader2 
} from "lucide-react";
import { notifySuccess, notifyError } from "../utils/alerts";

export const SetupWizardPage: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [searchAgent, setSearchAgent] = useState("");

  // Step 1: Selected Agent state
  const [selectedAgent, setSelectedAgent] = useState<any | null>(null);
  const [customPath, setCustomPath] = useState("");

  // Step 2: Selected Provider state
  const [selectedProvider, setSelectedProvider] = useState<any | null>(null);
  const [apiFormat, setApiFormat] = useState("openai");
  const [baseUrl, setBaseUrl] = useState("");
  const [providerName, setProviderName] = useState("");

  // Step 3: API Key & Model state
  const [apiKey, setApiKey] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [customModel, setCustomModel] = useState("");

  // Fetch supported agents
  const { data: agents, isLoading: loadingAgents } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/agents");
      return res.data;
    }
  });

  // Fetch active providers
  const { data: providers } = useQuery({
    queryKey: ["providers"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/providers");
      return res.data;
    }
  });

  // Fetch models for Selected Provider
  const { data: models } = useQuery({
    queryKey: ["models", selectedProvider?.id],
    queryFn: async () => {
      if (!selectedProvider?.id) return [];
      const res = await apiClient.get("/api/v1/models");
      return res.data.filter((m: any) => m.provider_id === selectedProvider.id);
    },
    enabled: !!selectedProvider?.id
  });

  // Trigger Provider Creation Mutation
  const createProviderMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await apiClient.post("/api/v1/providers", payload);
      return res.data;
    }
  });

  // Trigger API Key Creation Mutation
  const createKeyMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await apiClient.post("/api/v1/keys", payload);
      return res.data;
    }
  });

  // Wiring Mutation
  const wireMutation = useMutation({
    mutationFn: async (payload: { slug: string; base_url: string; api_key: string; model: string; custom_path?: string }) => {
      const res = await apiClient.post(`/api/v1/agents/${payload.slug}/wire`, payload);
      return res.data;
    }
  });

  // Complete Setup Wizard Mutation
  const completeSetupMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post("/api/v1/agents/complete-setup");
    },
    onSuccess: () => {
      notifySuccess("AI Gateway Pro setup completed successfully!");
      navigate("/");
    },
    onError: () => {
      notifyError("Failed to save setup wizard completion flag.");
    }
  });

  // Populate default provider configs
  const handleSelectProviderType = (type: string) => {
    setApiFormat(type);
    if (type === "openai") {
      setBaseUrl("https://api.openai.com/v1");
      setProviderName("OpenAI");
    } else if (type === "anthropic") {
      setBaseUrl("https://api.anthropic.com");
      setProviderName("Anthropic");
    } else if (type === "google") {
      setBaseUrl("https://generativelanguage.googleapis.com");
      setProviderName("Google Gemini");
    } else if (type === "groq") {
      setBaseUrl("https://api.groq.com/openai/v1");
      setProviderName("Groq");
    } else if (type === "deepseek") {
      setBaseUrl("https://api.deepseek.com");
      setProviderName("DeepSeek");
    } else if (type === "openrouter") {
      setBaseUrl("https://openrouter.ai/api/v1");
      setProviderName("OpenRouter");
    } else if (type === "ollama") {
      setBaseUrl("http://localhost:11434");
      setProviderName("Ollama");
    } else {
      setBaseUrl("");
      setProviderName("");
    }
  };

  const handleNextStep = () => {
    if (step === 1 && !selectedAgent) {
      notifyError("Please select a coding agent to continue.");
      return;
    }
    if (step === 2 && !selectedProvider && !providerName) {
      notifyError("Please select or enter an AI provider.");
      return;
    }
    setStep((prev) => prev + 1);
  };

  const handlePrevStep = () => {
    setStep((prev) => prev - 1);
  };

  const handleWireAndComplete = async () => {
    try {
      let finalProvider = selectedProvider;
      let finalKey = apiKey;

      // 1. Create provider if custom config filled
      if (!finalProvider) {
        const provPayload = {
          name: providerName,
          api_format: apiFormat,
          base_url: baseUrl,
          is_active: true,
          config: {}
        };
        finalProvider = await createProviderMutation.mutateAsync(provPayload);
      }

      // 2. Create API key inside database
      if (finalKey && finalProvider?.id) {
        const keyPayload = {
          provider_id: finalProvider.id,
          name: `${selectedAgent?.name || "Agent"} Key`,
          key: finalKey,
          priority: 1,
          is_enabled: true,
          rotation_policy: "priority"
        };
        await createKeyMutation.mutateAsync(keyPayload);
      }

      // 3. Trigger automatic config wiring
      const targetModel = selectedModel || customModel || "gpt-4o";
      // We route the agent requests to local gateway running on 8080
      const localGatewayUrl = `${window.location.protocol}//${window.location.hostname}:8080/v1`;
      
      await wireMutation.mutateAsync({
        slug: selectedAgent.slug,
        base_url: localGatewayUrl,
        api_key: "sk-ant-aigateway-pro-rotation-key", // standard loop key
        model: targetModel,
        custom_path: customPath || undefined
      });

      // 4. Complete Wizard
      await completeSetupMutation.mutateAsync();
    } catch (e: any) {
      notifyError(e.response?.data?.detail || "An error occurred during agent wiring.");
    }
  };

  const filteredAgents = agents?.filter((a: any) =>
    a.name.toLowerCase().includes(searchAgent.toLowerCase())
  ) || [];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-between text-slate-900 dark:text-slate-100 transition-colors duration-300">
      {/* Premium Header */}
      <header className="px-8 py-6 flex items-center justify-between border-b border-slate-200 dark:border-slate-900 bg-white/50 dark:bg-slate-950/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-violet-600 via-indigo-600 to-sky-600 bg-clip-text text-transparent">
              AI Gateway Pro
            </h1>
            <p className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">Setup Wizard</p>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2 text-xs font-semibold">
            {[1, 2, 3, 4].map((s) => (
              <React.Fragment key={s}>
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                    s === step 
                      ? "bg-violet-600 text-white shadow-lg shadow-violet-500/20 ring-4 ring-violet-500/20" 
                      : s < step 
                        ? "bg-emerald-500 text-white" 
                        : "bg-slate-200 dark:bg-slate-800 text-slate-500"
                  }`}
                >
                  {s < step ? <Check className="w-4 h-4" /> : s}
                </div>
                {s < 4 && <div className={`w-8 h-0.5 ${s < step ? "bg-emerald-500" : "bg-slate-200 dark:bg-slate-800"}`} />}
              </React.Fragment>
            ))}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-12 flex flex-col justify-center">
        {step === 1 && (
          <div className="space-y-6">
            <div className="text-center max-w-xl mx-auto space-y-2">
              <h2 className="text-3xl font-extrabold tracking-tight">Select Coding Agent</h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                Choose the coding agent you want to auto-configure. We will wire up environment settings to route request loads through the AI rotation gateway.
              </p>
            </div>

            {/* Search */}
            <div className="max-w-md mx-auto relative">
              <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
              <input
                type="text"
                placeholder="Search coding agents..."
                value={searchAgent}
                onChange={(e) => setSearchAgent(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              />
            </div>

            {loadingAgents ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-violet-600" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {filteredAgents.map((agent: any) => (
                  <div
                    key={agent.slug}
                    onClick={() => {
                      setSelectedAgent(agent);
                      if (agent.slug !== "custom") setCustomPath("");
                    }}
                    className={`relative p-5 rounded-2xl border cursor-pointer transition-all duration-300 flex flex-col justify-between h-40 ${
                      selectedAgent?.slug === agent.slug
                        ? "border-violet-600 bg-violet-600/5 dark:bg-violet-600/10 shadow-lg shadow-violet-500/5"
                        : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                          <Cpu className="w-5 h-5 text-violet-600" />
                        </div>
                        {agent.exists && (
                          <span className="text-[10px] bg-emerald-500/15 text-emerald-500 py-0.5 px-2 rounded-full font-bold">
                            Detected
                          </span>
                        )}
                      </div>
                      <h3 className="font-bold text-base">{agent.name}</h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                        {agent.config_path || "Custom Config Path"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Custom Path Field */}
            {selectedAgent?.slug === "custom" && (
              <div className="max-w-md mx-auto space-y-2 pt-4">
                <label className="text-xs font-semibold text-slate-500">Custom Agent Configuration File Path</label>
                <input
                  type="text"
                  placeholder="e.g. C:\Users\Username\.agent\config.json"
                  value={customPath}
                  onChange={(e) => setCustomPath(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-sm"
                />
              </div>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6 max-w-2xl mx-auto w-full">
            <div className="text-center space-y-2">
              <h2 className="text-3xl font-extrabold tracking-tight">Select AI Provider</h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                Choose an existing provider or create/override configurations for a new provider.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <label className="text-xs font-bold text-slate-500">Standard Providers</label>
                <div className="grid grid-cols-2 gap-2">
                  {["openai", "anthropic", "google", "groq", "deepseek", "openrouter", "ollama"].map((prov) => (
                    <button
                      key={prov}
                      type="button"
                      onClick={() => {
                        setSelectedProvider(null);
                        handleSelectProviderType(prov);
                      }}
                      className={`p-3 rounded-xl text-left border text-xs font-bold capitalize transition-colors ${
                        apiFormat === prov && !selectedProvider
                          ? "border-violet-600 bg-violet-600/5 dark:bg-violet-600/10 text-violet-600"
                          : "border-slate-200 dark:border-slate-800 hover:border-slate-300 bg-white dark:bg-slate-900"
                      }`}
                    >
                      {prov}
                    </button>
                  ))}
                </div>
              </div>

              {providers && providers.length > 0 && (
                <div className="space-y-3">
                  <label className="text-xs font-bold text-slate-500">Existing Configured Providers</label>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {providers.map((p: any) => (
                      <div
                        key={p.id}
                        onClick={() => {
                          setSelectedProvider(p);
                          setProviderName(p.name);
                          setApiFormat(p.api_format);
                          setBaseUrl(p.base_url);
                        }}
                        className={`p-3 rounded-xl border text-left cursor-pointer transition-colors ${
                          selectedProvider?.id === p.id
                            ? "border-violet-600 bg-violet-600/5 dark:bg-violet-600/10"
                            : "border-slate-200 dark:border-slate-800 hover:border-slate-300 bg-white dark:bg-slate-900"
                        }`}
                      >
                        <h4 className="font-bold text-xs">{p.name}</h4>
                        <p className="text-[10px] text-slate-500 truncate">{p.base_url}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Custom URL Override */}
            <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-900">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">Provider Name</label>
                  <input
                    type="text"
                    placeholder="e.g. OpenAI Cloud"
                    value={providerName}
                    disabled={!!selectedProvider}
                    onChange={(e) => setProviderName(e.target.value)}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-xs"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">API Format</label>
                  <select
                    value={apiFormat}
                    disabled={!!selectedProvider}
                    onChange={(e) => setApiFormat(e.target.value)}
                    className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-xs"
                  >
                    <option value="openai">OpenAI Compatible</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="google">Google Gemini</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500">API Base URL</label>
                <input
                  type="text"
                  placeholder="https://api.openai.com/v1"
                  value={baseUrl}
                  disabled={!!selectedProvider}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-xs"
                />
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6 max-w-xl mx-auto w-full">
            <div className="text-center space-y-2">
              <h2 className="text-3xl font-extrabold tracking-tight">Credentials & Model</h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                Provide your API Key. We will encrypt it locally and configure the default model for agent interactions.
              </p>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500">API Key Credentials</label>
                <div className="relative">
                  <Key className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
                  <input
                    type="password"
                    placeholder="Enter API key credential..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-xs"
                  />
                </div>
              </div>

              {selectedProvider && models && models.length > 0 ? (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">Target Model</label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-xs"
                  >
                    <option value="">Select a model...</option>
                    {models.map((m: any) => (
                      <option key={m.id} value={m.name}>
                        {m.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-500">Model Name Override</label>
                  <input
                    type="text"
                    placeholder="e.g. gpt-4o, claude-3-5-sonnet-20241022"
                    value={customModel}
                    onChange={(e) => setCustomModel(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-violet-500/50 text-xs"
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-8 max-w-xl mx-auto w-full text-center">
            <div className="space-y-3">
              <div className="w-16 h-16 rounded-full bg-violet-600/10 text-violet-600 flex items-center justify-center mx-auto shadow-inner">
                <Wrench className="w-8 h-8 animate-bounce" />
              </div>
              <h2 className="text-3xl font-extrabold tracking-tight">Ready to Configure</h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                We will automatically back up your existing config file and rewrite parameters to route your agent request loads through AI Gateway Pro.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-left space-y-4">
              <h3 className="font-bold text-xs text-slate-400 tracking-wider uppercase">Setup Summary</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Target Agent:</span>
                  <span className="font-bold">{selectedAgent?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">AI Provider:</span>
                  <span className="font-bold">{providerName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Format:</span>
                  <span className="font-bold uppercase">{apiFormat}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Target Model:</span>
                  <span className="font-bold">{selectedModel || customModel || "gpt-4o"}</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleWireAndComplete}
              disabled={wireMutation.isPending || completeSetupMutation.isPending}
              className="w-full py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-2xl font-bold text-sm shadow-xl shadow-violet-500/20 flex items-center justify-center space-x-2 transition-all"
            >
              {wireMutation.isPending || completeSetupMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Wiring Agent Configs...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>Complete Wiring & Finish Setup</span>
                </>
              )}
            </button>
          </div>
        )}
      </main>

      {/* Premium Navigation Controls */}
      <footer className="px-8 py-6 border-t border-slate-200 dark:border-slate-900 bg-white/50 dark:bg-slate-950/50 backdrop-blur-xl flex items-center justify-between sticky bottom-0 z-50">
        <button
          onClick={handlePrevStep}
          disabled={step === 1}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 font-semibold text-xs transition-colors disabled:opacity-30 disabled:pointer-events-none"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back</span>
        </button>

        {step < 4 ? (
          <button
            onClick={handleNextStep}
            className="flex items-center space-x-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-violet-500/10 transition-colors"
          >
            <span>Continue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <div />
        )}
      </footer>
    </div>
  );
};
