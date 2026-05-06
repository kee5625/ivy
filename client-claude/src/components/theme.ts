export type PaletteKey = "manuscript";

type PaletteTokens = Record<string, string>;

export const IVY_PALETTES: Record<PaletteKey, { label: string; accent: string; tokens: PaletteTokens }> = {
  manuscript: {
    label: "Manuscript",
    accent: "oklch(0.48 0.13 25)",
    tokens: {
      "--ivy-bg":         "oklch(0.975 0.008 75)",
      "--ivy-bgRaised":   "oklch(0.99 0.005 75)",
      "--ivy-bgInk":      "oklch(0.965 0.012 70)",
      "--ivy-panel":      "oklch(0.945 0.014 70)",
      "--ivy-rule":       "oklch(0.86 0.012 70)",
      "--ivy-ruleSoft":   "oklch(0.92 0.01 70)",
      "--ivy-ink":        "oklch(0.22 0.012 60)",
      "--ivy-inkDeep":    "oklch(0.14 0.014 60)",
      "--ivy-inkMute":    "oklch(0.48 0.012 60)",
      "--ivy-inkFaint":   "oklch(0.62 0.01 60)",
      "--ivy-accent":     "oklch(0.48 0.13 25)",
      "--ivy-accentSoft": "oklch(0.92 0.04 25)",
      "--ivy-accentInk":  "oklch(0.32 0.10 25)",
      "--ivy-sevHigh":    "oklch(0.48 0.13 25)",
      "--ivy-sevMed":     "oklch(0.62 0.12 70)",
      "--ivy-sevLow":     "oklch(0.55 0.04 70)",
    },
  },
};

export function applyPalette(key: PaletteKey): void {
  const { tokens } = IVY_PALETTES[key];
  const root = document.documentElement;
  for (const [k, v] of Object.entries(tokens)) {
    root.style.setProperty(k, v);
  }
}
