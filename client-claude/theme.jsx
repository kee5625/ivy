/* Ivy theme tokens — three palettes selectable via Tweaks.
   All neutrals stay at chroma <= 0.015. Each palette has a single accent. */

const IVY_PALETTES = {
  manuscript: {
    label: "Manuscript",
    description: "warm paper, ink black, oxblood",
    bg:        "oklch(0.975 0.008 75)",   // warm paper
    bgRaised:  "oklch(0.99 0.005 75)",
    bgInk:     "oklch(0.965 0.012 70)",   // tinted card
    panel:     "oklch(0.945 0.014 70)",
    rule:      "oklch(0.86 0.012 70)",
    ruleSoft:  "oklch(0.92 0.01 70)",
    ink:       "oklch(0.22 0.012 60)",    // body
    inkDeep:   "oklch(0.14 0.014 60)",    // headings
    inkMute:   "oklch(0.48 0.012 60)",
    inkFaint:  "oklch(0.62 0.01 60)",
    accent:    "oklch(0.48 0.13 25)",     // oxblood
    accentSoft:"oklch(0.92 0.04 25)",
    accentInk: "oklch(0.32 0.10 25)",
    sev_high:   "oklch(0.48 0.13 25)",
    sev_med:    "oklch(0.62 0.12 70)",
    sev_low:    "oklch(0.55 0.04 70)",
  },
  archive: {
    label: "Archive",
    description: "cool grey, deep navy ink, brass",
    bg:        "oklch(0.965 0.006 240)",   // archival paper
    bgRaised:  "oklch(0.992 0.003 240)",   // card surface
    bgInk:     "oklch(0.945 0.011 240)",   // tinted card
    panel:     "oklch(0.92 0.013 240)",
    rule:      "oklch(0.81 0.014 240)",    // stronger hairline
    ruleSoft:  "oklch(0.89 0.01 240)",
    ink:       "oklch(0.26 0.045 252)",    // body navy
    inkDeep:   "oklch(0.13 0.055 252)",    // deep navy
    inkMute:   "oklch(0.46 0.028 250)",
    inkFaint:  "oklch(0.6 0.018 250)",
    accent:    "oklch(0.58 0.13 70)",      // richer brass
    accentSoft:"oklch(0.91 0.05 75)",
    accentInk: "oklch(0.38 0.11 70)",
    sev_high:   "oklch(0.5 0.16 25)",      // crimson
    sev_med:    "oklch(0.6 0.13 70)",      // amber-brass
    sev_low:    "oklch(0.55 0.03 240)",    // navy-grey
  },
  slate: {
    label: "Slate",
    description: "true neutrals, cobalt accent",
    bg:        "oklch(0.97 0.003 250)",
    bgRaised:  "oklch(0.99 0.002 250)",
    bgInk:     "oklch(0.955 0.005 250)",
    panel:     "oklch(0.935 0.006 250)",
    rule:      "oklch(0.84 0.006 250)",
    ruleSoft:  "oklch(0.91 0.005 250)",
    ink:       "oklch(0.22 0.008 250)",
    inkDeep:   "oklch(0.13 0.01 250)",
    inkMute:   "oklch(0.46 0.008 250)",
    inkFaint:  "oklch(0.6 0.006 250)",
    accent:    "oklch(0.5 0.13 250)",     // cobalt
    accentSoft:"oklch(0.93 0.04 250)",
    accentInk: "oklch(0.34 0.11 250)",
    sev_high:   "oklch(0.5 0.13 25)",
    sev_med:    "oklch(0.6 0.1 75)",
    sev_low:    "oklch(0.55 0.02 250)",
  },
};

function applyPalette(name) {
  const p = IVY_PALETTES[name] || IVY_PALETTES.manuscript;
  const root = document.documentElement;
  Object.entries(p).forEach(([k, v]) => {
    if (typeof v === "string" && v.startsWith("oklch")) {
      root.style.setProperty(`--ivy-${k}`, v);
    }
  });
}

window.IVY_PALETTES = IVY_PALETTES;
window.applyIvyPalette = applyPalette;
