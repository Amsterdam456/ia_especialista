import type { ReactNode } from "react";

type Props = {
  sidebar: ReactNode;
  children: ReactNode;
};

export function Shell({ sidebar, children }: Props) {
  return (
    <div className="shell">
      {sidebar}
      <main className="shell-main">{children}</main>
    </div>
  );
}
