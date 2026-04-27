export type PaletteKey = "manuscript" | "archive" | "slate";

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
  archive: {
    label: "Archive",
    accent: "oklch(0.58 0.13 70)",
    tokens: {
      "--ivy-bg":         "oklch(0.965 0.006 240)",
      "--ivy-bgRaised":   "oklch(0.992 0.003 240)",
      "--ivy-bgInk":      "oklch(0.945 0.011 240)",
      "--ivy-panel":      "oklch(0.92 0.013 240)",
      "--ivy-rule":       "oklch(0.81 0.014 240)",
      "--ivy-ruleSoft":   "oklch(0.89 0.01 240)",
      "--ivy-ink":        "oklch(0.26 0.045 252)",
      "--ivy-inkDeep":    "oklch(0.13 0.055 252)",
      "--ivy-inkMute":    "oklch(0.46 0.028 250)",
      "--ivy-inkFaint":   "oklch(0.6 0.018 250)",
      "--ivy-accent":     "oklch(0.58 0.13 70)",
      "--ivy-accentSoft": "oklch(0.91 0.05 75)",
      "--ivy-accentInk":  "oklch(0.38 0.11 70)",
      "--ivy-sevHigh":    "oklch(0.5 0.16 25)",
      "--ivy-sevMed":     "oklch(0.6 0.13 70)",
      "--ivy-sevLow":     "oklch(0.55 0.03 240)",
    },
  },
  slate: {
    label: "Slate",
    accent: "oklch(0.5 0.13 250)",
    tokens: {
      "--ivy-bg":         "oklch(0.97 0.003 250)",
      "--ivy-bgRaised":   "oklch(0.99 0.002 250)",
      "--ivy-bgInk":      "oklch(0.955 0.005 250)",
      "--ivy-panel":      "oklch(0.935 0.006 250)",
      "--ivy-rule":       "oklch(0.84 0.006 250)",
      "--ivy-ruleSoft":   "oklch(0.91 0.005 250)",
      "--ivy-ink":        "oklch(0.22 0.008 250)",
      "--ivy-inkDeep":    "oklch(0.13 0.01 250)",
      "--ivy-inkMute":    "oklch(0.46 0.008 250)",
      "--ivy-inkFaint":   "oklch(0.6 0.006 250)",
      "--ivy-accent":     "oklch(0.5 0.13 250)",
      "--ivy-accentSoft": "oklch(0.93 0.04 250)",
      "--ivy-accentInk":  "oklch(0.34 0.11 250)",
      "--ivy-sevHigh":    "oklch(0.5 0.13 25)",
      "--ivy-sevMed":     "oklch(0.6 0.1 75)",
      "--ivy-sevLow":     "oklch(0.55 0.02 250)",
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
