import type { ButtonHTMLAttributes, ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "ghost";
};

export function GlassButton({ children, variant = "primary", className = "", ...rest }: Props) {
  const base = "glass-button";
  const ghost = "ghost"; // opcional, vira glass-button ghost
  return (
    <button
      className={`${base} ${variant === "ghost" ? ghost : ""} ${className}`.trim()}
      {...rest}
    >
      {children}
    </button>
  );
}