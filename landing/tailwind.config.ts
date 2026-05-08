import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./content/**/*.{js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        night: {
          DEFAULT: "#0D0B1E",
          900: "#0A0818",
          800: "#16122E",
          700: "#1E1A3E",
          600: "#2A2450",
          500: "#3D3670",
        },
        gold: {
          DEFAULT: "#C89B3C",
          light: "#E8C96A",
          dim: "#9B7530",
          subtle: "rgba(200,155,60,0.15)",
        },
        accent: {
          DEFAULT: "#7C3AED",
          soft: "#4F46E5",
        },
        prose: {
          DEFAULT: "#F0EDFF",
          muted: "#8B87A8",
          faint: "#5A5680",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-inter)",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      backgroundImage: {
        "hero-glow":
          "radial-gradient(ellipse 80% 60% at 15% 50%, #1E1A3E 0%, #0D0B1E 65%)",
        "cta-gradient":
          "linear-gradient(135deg, #7C3AED 0%, #4F46E5 60%, #2563EB 100%)",
        "gold-gradient":
          "linear-gradient(90deg, #C89B3C 0%, #E8C96A 50%, #C89B3C 100%)",
      },
      animation: {
        "hero-pulse": "heroPulse 12s ease-in-out infinite",
        "fade-up": "fadeUp 0.6s ease-out both",
        shimmer: "shimmer 2.5s linear infinite",
      },
      keyframes: {
        heroPulse: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      boxShadow: {
        gold: "0 0 40px rgba(200,155,60,0.15)",
        "gold-sm": "0 0 16px rgba(200,155,60,0.2)",
        card: "0 4px 32px rgba(0,0,0,0.4)",
      },
    },
  },
  plugins: [],
};

export default config;
