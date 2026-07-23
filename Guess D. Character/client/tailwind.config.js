/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      colors: {
        background: "#0F172A",
        surface: "#1E293B",
        surfaceHover: "#334155",

        text: {
          primary: "#F8FAFC",
          secondary: "#94A3B8",
        },

        accent: {
          DEFAULT: "#F59E0B",
          hover: "#D97706",
        },

        success: {
          DEFAULT: "#22C55E",
          bg: "#052E16",
        },

        danger: {
          DEFAULT: "#EF4444",
          bg: "#450A0A",
        },

        border: "#334155",
      },

      boxShadow: {
        card: "0 8px 24px rgba(0,0,0,0.25)",
      },

      borderRadius: {
        card: "14px",
      },

      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
      },

      animation: {
        "fade-in": "fadeIn 0.25s ease-out",
        "shake": "shake 0.3s ease-in-out",
      },

      keyframes: {
        fadeIn: {
          "0%": {
            opacity: "0",
            transform: "translateY(8px)",
          },
          "100%": {
            opacity: "1",
            transform: "translateY(0)",
          },
        },

        shake: {
          "0%,100%": {
            transform: "translateX(0)",
          },
          "25%": {
            transform: "translateX(-6px)",
          },
          "75%": {
            transform: "translateX(6px)",
          },
        },
      },
    },
  },

  plugins: [],
}