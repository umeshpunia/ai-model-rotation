import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { Loader2 } from "lucide-react";
import { apiClient } from "./api/client";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/Login";
import { DashboardPage } from "./pages/Dashboard";
import { ProvidersPage } from "./pages/Providers";
import { ApiKeysPage } from "./pages/ApiKeys";
import { LogsPage } from "./pages/Logs";
import { SettingsPage } from "./pages/Settings";
import { SetupWizardPage } from "./pages/SetupWizard";

// TanStack Query Client configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const SetupWizardGuard: React.FC = () => {
  const { data: statusData, isLoading } = useQuery({
    queryKey: ["statusCheck"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/status");
      return res.data;
    },
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-violet-600" />
      </div>
    );
  }

  if (statusData && statusData.setup_wizard_completed === false) {
    return <Navigate to="/wizard" replace />;
  }

  return <Outlet />;
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" />
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Setup Wizard Route */}
          <Route path="/wizard" element={<SetupWizardPage />} />

          {/* Secure Router Layout Group */}
          <Route element={<SetupWizardGuard />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="providers" element={<ProvidersPage />} />
              <Route path="keys" element={<ApiKeysPage />} />
              <Route path="logs" element={<LogsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
