import type { ReactNode } from "react";

type Props = {
  background?: string;
  sidebar: ReactNode;
  children: ReactNode;
};

export function Shell({ sidebar, children, background }: Props) {
  return (
    <div
      className="shell"
      style={
        background
          ? { backgroundImage: `linear-gradient(135deg, #0b1224 0%, #0f1b35 50%, #0b1224 100%), url(${background})` }
          : {}
      }
    >
      {sidebar}
      <main className="shell-main">{children}</main>
    </div>
  );
}

