import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f2f7ff",
          100: "#e0edff",
          200: "#bcd5ff",
          300: "#8ab6ff",
          400: "#5990ff",
          500: "#366bff",
          600: "#204dfa",
          700: "#1538d7",
          800: "#132fa7",
          900: "#132a7f",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "\"Segoe UI\"",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;

