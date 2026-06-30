import Swal from "sweetalert2";
import toast from "react-hot-toast";

// Toast helpers
export const notifySuccess = (message: string) => {
  toast.success(message, {
    style: {
      background: document.documentElement.classList.contains("dark") ? "#0f172a" : "#fff",
      color: document.documentElement.classList.contains("dark") ? "#fff" : "#0f172a",
      borderRadius: "12px",
      border: document.documentElement.classList.contains("dark") ? "1px solid #1e293b" : "1px solid #e2e8f0",
    },
  });
};

export const notifyError = (message: string) => {
  toast.error(message, {
    style: {
      background: document.documentElement.classList.contains("dark") ? "#0f172a" : "#fff",
      color: document.documentElement.classList.contains("dark") ? "#fff" : "#0f172a",
      borderRadius: "12px",
      border: document.documentElement.classList.contains("dark") ? "1px solid #1e293b" : "1px solid #e2e8f0",
    },
  });
};

// SweetAlert2 Confirmation helper
export const confirmAction = async (options: {
  title: string;
  text: string;
  confirmButtonText?: string;
  cancelButtonText?: string;
}) => {
  const isDark = document.documentElement.classList.contains("dark");
  
  const result = await Swal.fire({
    title: options.title,
    text: options.text,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: options.confirmButtonText || "Confirm",
    cancelButtonText: options.cancelButtonText || "Cancel",
    confirmButtonColor: "#8b5cf6", // premium violet color
    cancelButtonColor: "#ef4444", // rose color
    background: isDark ? "#0f172a" : "#ffffff",
    color: isDark ? "#ffffff" : "#0f172a",
    customClass: {
      popup: "rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl",
      title: "font-semibold text-lg text-slate-900 dark:text-white",
      confirmButton: "px-4 py-2.5 rounded-xl font-semibold text-sm transition-all",
      cancelButton: "px-4 py-2.5 rounded-xl font-semibold text-sm transition-all",
    },
  });
  
  return result.isConfirmed;
};
