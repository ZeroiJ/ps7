"use client";

import { useEffect, useState, useCallback } from "react";

interface ToastProps {
  message: string;
  type: "error" | "success" | "info";
  onClose: () => void;
}

export default function Toast({ message, type, onClose }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  const dismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(onClose, 300);
  }, [onClose]);

  useEffect(() => {
    const timer = setTimeout(dismiss, 5000);
    return () => clearTimeout(timer);
  }, [dismiss]);

  const bgColor =
    type === "error"
      ? "bg-chroma-error"
      : type === "success"
      ? "bg-chroma-success"
      : "bg-chroma-primary";

  return (
    <div
      className={`fixed top-20 right-6 z-50 max-w-sm ${
        isExiting ? "animate-slide-out" : "animate-slide-in"
      }`}
    >
      <div
        className={`${bgColor} text-white px-4 py-3 rounded-lg flex items-center gap-3`}
      >
        <span className="text-sm flex-1">{message}</span>
        <button
          onClick={dismiss}
          className="text-white/80 hover:text-white transition-colors cursor-pointer"
          aria-label="Close"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M4 4L12 12M12 4L4 12"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
