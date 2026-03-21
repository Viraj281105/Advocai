import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["DM Serif Display", "Georgia", "serif"],
        body: ["DM Sans", "sans-serif"],
      },
      colors: {
        purple: {
          950: "#0f0a1e",
          900: "#1a1040",
          800: "#2d1b69",
          700: "#3d2494",
          600: "#4f31b8",
          500: "#6347d4",
          400: "#8b6fe8",
          300: "#b39ef4",
          200: "#d4c7fa",
          100: "#ede8fd",
          50:  "#f7f4ff",
        },
        gold: {
          DEFAULT: "#c9a84c",
          light: "#e8c97a",
        },
        cream: "#faf8f2",
      },
    },
  },
  plugins: [],
};

export default config;
