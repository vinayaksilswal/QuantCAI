import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        inter: ['Inter', 'sans-serif'],
      },
      colors: {
        // These were hardcoded hex values that drifted from the CSS custom
        // properties in index.css, so 'qc-surface' and 'bg-card' rendered as
        // different colours. They now read the same tokens, giving one source
        // of truth for the palette.
        'qc-bg': 'hsl(var(--qc-bg))',
        'qc-bg-raised': 'hsl(var(--qc-bg-raised))',
        'qc-surface': 'hsl(var(--qc-surface))',
        'qc-surface-hover': 'hsl(var(--qc-surface-hover))',
        'qc-border': 'hsl(var(--qc-border))',
        'qc-border-strong': 'hsl(var(--qc-border-strong))',
        'qc-text': 'hsl(var(--qc-text))',
        'qc-muted': 'hsl(var(--qc-text-muted))',
        'qc-subtle': 'hsl(var(--qc-text-subtle))',
        'qc-accent': 'hsl(var(--qc-brand))',
        'qc-accent-hover': 'hsl(var(--qc-brand-hover))',
        'qc-accent-fg': 'hsl(var(--qc-brand-fg))',
        'qc-accent-dim': 'hsl(var(--qc-brand) / 0.12)',
        'qc-danger': 'hsl(var(--qc-danger))',
        'qc-warn': 'hsl(var(--qc-warn))',
        'qc-ok': 'hsl(var(--qc-ok))',
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        // Neutral, low-spread shadows. The previous coloured glows
        // (shadow-purple-500/40 and friends) read as consumer marketing to
        // the security buyers this product is sold to.
        'qc-sm': '0 1px 2px 0 hsl(222 40% 2% / 0.4)',
        'qc': '0 4px 12px -2px hsl(222 40% 2% / 0.5)',
        'qc-lg': '0 12px 32px -8px hsl(222 40% 2% / 0.6)',
      },
      maxWidth: {
        measure: '68ch',
      },
    },
  },
  plugins: [],
};

export default config;
