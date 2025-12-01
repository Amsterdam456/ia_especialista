import type { ReactNode } from "react";

type Props = {
  title: string;
  description: string;
  tag?: string;
  icon?: ReactNode;
};

export function InfoCard({ title, description, tag, icon }: Props) {
  return (
    <article className="card-glass">
      <div className="card-icon">{icon}</div>
      <div className="card-title">{title}</div>
      <div className="card-description">{description}</div>
      {tag ? <div className="card-tag">{tag}</div> : null}
    </article>
  );
}
