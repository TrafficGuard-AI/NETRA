import { useSyncExternalStore } from "react";

// A tiny external store so every component (toggle, charts) stays in sync and
// the choice persists across reloads.
const KEY = "tg-theme";
const listeners = new Set();

const initial = () => {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* ignore */
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

let theme = initial();

const apply = (t) => document.documentElement.setAttribute("data-theme", t);
apply(theme);

export function setTheme(next) {
  theme = next;
  try {
    localStorage.setItem(KEY, next);
  } catch {
    /* ignore */
  }
  apply(next);
  listeners.forEach((l) => l());
}

export function toggleTheme() {
  setTheme(theme === "dark" ? "light" : "dark");
}

export function useTheme() {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => theme,
    () => "light"
  );
}
