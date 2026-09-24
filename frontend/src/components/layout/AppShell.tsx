import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-dvh overflow-hidden bg-[var(--color-bg)] text-[var(--color-text-primary)]">
      {/* WCAG 2.2 AA Skip Link for Keyboard Navigation */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar />
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto p-6 focus:outline-none"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
