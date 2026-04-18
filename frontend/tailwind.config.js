/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
        },
        status: {
          done: "#16a34a",
          running: "#0ea5e9",
          queued: "#eab308",
          error: "#dc2626",
        },
      },
    },
  },
  plugins: [],
};
