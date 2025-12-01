import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle: string;
  description?: string;
  primary?: boolean;
  onClick?: () => void;
  icon?: ReactNode;
  disabled?: boolean;
};

export function HomeActionCard({ title, subtitle, description, primary, onClick, icon, disabled }: Props) {
  return (
    <article
      className={`home-card ${primary ? "primary" : ""} ${disabled ? "disabled" : ""}`}
      onClick={disabled ? undefined : onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" && onClick && !disabled) onClick();
      }}
    >
      <div className="home-card-header">
        <div className="home-card-icon">{icon}</div>
        <div className="home-card-subtitle">{subtitle}</div>
      </div>
      <div className="home-card-title">{title}</div>
      {description ? <div className="home-card-description">{description}</div> : null}
      {disabled ? <div className="pill muted">Em breve</div> : null}
    </article>
  );
}
