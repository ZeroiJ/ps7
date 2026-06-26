"use client";

import { useEffect, useState } from "react";

interface ProgressStepperProps {
  currentStep: number;
  steps: string[];
}

export default function ProgressStepper({
  currentStep,
  steps,
}: ProgressStepperProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (s: number) => {
    const min = Math.floor(s / 60);
    const sec = s % 60;
    return `${min}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="w-full max-w-2xl mx-auto py-8">
      <div className="flex items-center justify-between relative">
        {steps.map((step, i) => {
          const isComplete = i < currentStep;
          const isActive = i === currentStep;

          return (
            <div
              key={step}
              className="flex flex-col items-center relative z-10 flex-1"
            >
              {/* Connector line */}
              {i < steps.length - 1 && (
                <div
                  className="absolute top-3 left-1/2 w-full h-px"
                  style={{ backgroundColor: i < currentStep ? "#141414" : "#e8e8e8" }}
                />
              )}

              {/* Circle */}
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center relative ${
                  isComplete
                    ? "bg-chroma-primary"
                    : isActive
                    ? "bg-chroma-primary animate-pulse-ring"
                    : "border-2 border-chroma-border bg-white"
                }`}
              >
                {isComplete && (
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 12 12"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M2.5 6L5 8.5L9.5 3.5"
                      stroke="white"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>

              {/* Label */}
              <span
                className={`text-xs mt-2 text-center ${
                  isActive || isComplete
                    ? "text-chroma-fg font-medium"
                    : "text-chroma-muted-fg"
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>

      {/* Elapsed time */}
      <div className="text-center mt-6">
        <span className="text-sm text-chroma-muted-fg font-mono">
          {formatTime(elapsed)}
        </span>
      </div>

      {/* Progress bar */}
      <div className="mt-4 w-full h-1 bg-chroma-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-chroma-primary rounded-full transition-all duration-500"
          style={{
            width: `${((currentStep + 1) / steps.length) * 100}%`,
          }}
        />
      </div>
    </div>
  );
}
