import type { ButtonHTMLAttributes, ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "ghost";
};

export function GlassButton({ children, variant = "primary", className = "", ...rest }: Props) {
  const base =
    "rounded-full px-4 py-2 text-sm font-semibold transition-all duration-200 backdrop-blur-lg";
  const primary =
    "bg-gradient-to-r from-blue-500/70 via-sky-500/70 to-cyan-400/70 text-white shadow-glass hover:shadow-glass-strong hover:-translate-y-0.5 border border-white/10";
  const ghost =
    "bg-white/5 text-slate-200 border border-white/10 hover:bg-white/10 hover:-translate-y-0.5";

  return (
    <button
      className={`${base} ${variant === "primary" ? primary : ghost} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
