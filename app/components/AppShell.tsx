"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Archive, Cloud, Menu, Search, Upload, X } from "lucide-react";
import { useState } from "react";
import { Logo } from "./Logo";

const links = [
  { href: "/", label: "Library", icon: Archive },
  { href: "/search", label: "Search", icon: Search },
  { href: "/upload", label: "Upload", icon: Upload },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-top">
          <Logo />
          <button className="icon-button close-nav" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={19} /></button>
        </div>
        <nav aria-label="Primary navigation">
          {links.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link key={href} href={href} className={active ? "active" : ""} onClick={() => setOpen(false)}>
                <Icon size={18} strokeWidth={1.8} /> {label}
              </Link>
            );
          })}
        </nav>
        <div className="storage-card">
          <div className="storage-icon"><Cloud size={18} /></div>
          <div><strong>B2 is the library</strong><span>Media, metadata & manifests</span></div>
          <span className="status-dot" title="Demo fallback active" />
        </div>
        <div className="sidebar-disclaimer">Prototype · public, synthetic, reenacted, or user-created footage only.</div>
      </aside>
      {open && <button className="nav-scrim" aria-label="Close navigation" onClick={() => setOpen(false)} />}
      <main className="main-content">
        <div className="mobile-bar"><button className="icon-button" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu /></button><Logo /></div>
        {children}
      </main>
    </div>
  );
}

