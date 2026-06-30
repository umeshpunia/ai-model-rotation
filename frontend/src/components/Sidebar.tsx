import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Database,
  Key,
  History,
  Settings,
  LogOut,
  Sun,
  Moon,
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { useThemeStore } from "../store/themeStore";

export const Sidebar: React.FC = () => {
  const logout = useAuthStore((state) => state.logout);
  const username = useAuthStore((state) => state.username);
  const { theme, toggleTheme } = useThemeStore();

  const navItems = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/providers", label: "Providers", icon: Database },
    { to: "/keys", label: "API Keys", icon: Key },
    { to: "/logs", label: "Request Logs", icon: History },
    { to: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col justify-between border-r border-slate-800 backdrop-blur-md bg-opacity-95 h-screen sticky top-0">
      <div>
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-violet-500/25">
              G
            </div>
            <span className="font-semibold text-lg tracking-wider text-white">
              AI Gateway Pro
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-2.5 rounded-xl transition-all duration-200 group text-sm ${
                  isActive
                    ? "bg-violet-600 text-white font-medium shadow-md shadow-violet-600/10"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                }`
              }
            >
              <item.icon className="w-4 h-4 transition-transform group-hover:scale-110" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Footer / User Profile */}
      <div className="p-4 border-t border-slate-800 space-y-4">
        {/* Theme Toggle & Profile info */}
        <div className="flex items-center justify-between px-2">
          <div className="text-xs text-slate-500">
            Signed in as <span className="text-slate-300 font-semibold">{username}</span>
          </div>
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Toggle Theme"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-sm text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Log Out</span>
        </button>
      </div>
    </aside>
  );
};
