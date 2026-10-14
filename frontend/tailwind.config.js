/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // ── New cinematic dark-navy / teal-accent palette ──────────────────
        // Page background — deepest layer
        "background":                  "#101321",
        // Cards, modals, sidebars, auth panel — one step above background
        "surface":                     "#1C1E2D",
        "surface-container":           "#1C1E2D",
        "surface-container-low":       "#161825",
        "surface-container-high":      "#22243A",
        "surface-container-lowest":    "#0C0E1A",
        "surface-container-highest":   "#2A2D3D",
        "surface-dim":                 "#0C0E1A",
        "surface-bright":              "#2A2D3D",
        "surface-variant":             "#1C1E2D",
        // Foreground — pure white headings / primary text
        "on-background":               "#FFFFFF",
        "on-surface":                  "#FFFFFF",
        "on-surface-variant":          "#9CA3AF",
        // Primary accent — vivid mint-teal
        "primary":                     "#40CCB7",
        "on-primary":                  "#002E28",
        "primary-container":           "#40CCB799",
        "primary-fixed":               "#40CCB7",
        "primary-fixed-dim":           "#2EAA97",
        "inverse-primary":             "#002E28",
        "surface-tint":                "#40CCB7",
        // Secondary / muted
        "secondary":                   "#1C1E2D",
        "on-secondary":                "#FFFFFF",
        "secondary-container":         "#1C1E2D",
        "on-secondary-container":      "#9CA3AF",
        "secondary-fixed":             "#2A2D3D",
        "secondary-fixed-dim":         "#1C1E2D",
        "on-secondary-fixed":          "#FFFFFF",
        "on-secondary-fixed-variant":  "#9CA3AF",
        // Muted foreground — body text, descriptions, placeholders
        "muted":                       "#1C1E2D",
        "muted-foreground":            "#6B7280",
        // Labels — form labels, secondary labels
        "label":                       "#9CA3AF",
        // Borders — thin dark-slate
        "outline":                     "#2A2D3D",
        "outline-variant":             "#5C5F78",
        // Destructive — errors / delete
        "error":                       "#EF4444",
        "on-error":                    "#FFFFFF",
        "error-container":             "rgba(239,68,68,0.15)",
        "on-error-container":          "#FECACA",
        // Inverse
        "inverse-surface":             "#FFFFFF",
        "inverse-on-surface":          "#101321",
        // Tertiary (kept for backward-compat, repurposed to teal-adjacent)
        "tertiary":                    "#2EAA97",
        "on-tertiary":                 "#FFFFFF",
        "tertiary-container":          "rgba(64,204,183,0.15)",
        "tertiary-fixed":              "#40CCB7",
        "tertiary-fixed-dim":          "#2EAA97",
        "on-tertiary-fixed":           "#002E28",
        "on-tertiary-fixed-variant":   "#005045",
        "on-tertiary-container":       "#40CCB7",
        // Legacy aliases kept so existing Tailwind classes don't break
        "on-primary-container":        "#40CCB7",
        "on-primary-fixed":            "#002E28",
        "on-primary-fixed-variant":    "#005045",
      },
      borderRadius: {
        "DEFAULT": "0.375rem",
        "lg":      "0.5rem",
        "xl":      "0.75rem",
        "2xl":     "1rem",
        "full":    "9999px",
      },
      spacing: {
        "margin-desktop": "32px",
        "container-max":  "1440px",
        "unit":           "4px",
        "gutter":         "24px",
        "margin-mobile":  "16px",
      },
      fontFamily: {
        // Headings — Space Grotesk (geometric / tech-forward)
        "display":            ["'Space Grotesk'", "system-ui", "sans-serif"],
        "headline-lg":        ["'Space Grotesk'", "system-ui", "sans-serif"],
        "headline-lg-mobile": ["'Space Grotesk'", "system-ui", "sans-serif"],
        "headline-md":        ["'Space Grotesk'", "system-ui", "sans-serif"],
        // Body — system stack
        "body-lg":    ["'SF Pro Display'", "'Segoe UI'", "system-ui", "sans-serif"],
        "body-sm":    ["'SF Pro Display'", "'Segoe UI'", "system-ui", "sans-serif"],
        // Mono
        "label-mono": ["'JetBrains Mono'", "monospace"],
      },
      fontSize: {
        "label-mono":        ["12px", { "lineHeight": "1",   "letterSpacing": "0.05em",  "fontWeight": "500" }],
        "display":           ["48px", { "lineHeight": "1.1", "letterSpacing": "-0.02em", "fontWeight": "700" }],
        "headline-md":       ["24px", { "lineHeight": "1.3", "fontWeight": "600" }],
        "body-lg":           ["16px", { "lineHeight": "1.6", "fontWeight": "400" }],
        "headline-lg-mobile":["24px", { "lineHeight": "1.2", "fontWeight": "600" }],
        "headline-lg":       ["32px", { "lineHeight": "1.2", "letterSpacing": "-0.01em", "fontWeight": "600" }],
        "body-sm":           ["14px", { "lineHeight": "1.5", "fontWeight": "400" }],
      },
      boxShadow: {
        // Teal glow for active / hover states
        "teal-glow":   "0 0 20px rgba(64,204,183,0.25)",
        "teal-glow-lg":"0 0 40px rgba(64,204,183,0.35)",
        "card":        "0 4px 24px rgba(0,0,0,0.35)",
      },
      keyframes: {
        "fade-in": {
          "0%":   { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-teal": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(64,204,183,0)" },
          "50%":      { boxShadow: "0 0 0 6px rgba(64,204,183,0.15)" },
        },
      },
      animation: {
        "fade-in":    "fade-in 0.3s ease both",
        "pulse-teal": "pulse-teal 2s ease-in-out infinite",
      },
    }
  },
  plugins: [],
}
