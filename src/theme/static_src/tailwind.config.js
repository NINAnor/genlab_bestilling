/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

const colors = require("tailwindcss/colors");

module.exports = {
  content: [
    /**
     * HTML. Paths to Django template files that will contain Tailwind CSS classes.
     */

    /*  Templates within theme app (<tailwind_app_name>/templates), e.g. base.html. */
    "../templates/**/*.html",

    /*
     * Main templates directory of the project (BASE_DIR/templates).
     * Adjust the following line to match your project structure.
     */
    "../../templates/**/*.html",

    /*
     * Templates in other django apps (BASE_DIR/<any_app_name>/templates).
     * Adjust the following line to match your project structure.
     */
    "../../**/templates/**/*.html",
    "../../**/**/templates/**/*.html",

    "../../../.venv/lib64/python3.11/site-packages/tailwind_ui/templates/**/*.html",
    "../../../.venv/lib64/python3.11/site-packages/formset/templates/formset/tailwind/**/*.html",
    "../../../.venv/lib64/python3.11/site-packages/formset/renders/tailwind.py",
    "../../../.venv/lib64/python3.11/site-packages/formset/templates/formset/tailwind/*.html",

    /**
     * JS: If you use Tailwind CSS in JavaScript, uncomment the following lines and make sure
     * patterns match your project structure.
     */
    /* JS 1: Ignore any JavaScript in node_modules folder. */
    "!../../**/node_modules",
    /* JS 2: Process all JavaScript files in the project. */
    "../../**/*.js",
    "../../**/*.jsx",

    /**
     * Python: If you use Tailwind CSS classes in Python, uncomment the following line
     * and make sure the pattern below matches your project structure.
     */
    "../../**/*.py",
  ],
  safelist: [
    "select2-selection--multiple", // ensure Tailwind keeps this
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "var(--color-brand-primary)",
          secondary: "var(--color-brand-secondary)",
        },
        primary: {
          DEFAULT: "var(--color-primary-500)",
          100: "var(--color-primary-100)",
          300: "var(--color-primary-300)",
          500: "var(--color-primary-500)",
          600: "var(--color-primary-600)",
          700: "var(--color-primary-700)",
          800: "var(--color-primary-800)",
        },
        secondary: {
          DEFAULT: "var(--color-secondary-500)",
          100: "var(--color-secondary-100)",
          300: "var(--color-secondary-300)",
          500: "var(--color-secondary-500)",
          600: "var(--color-secondary-600)",
          700: "var(--color-secondary-700)",
          800: "var(--color-secondary-800)",
        },
        tertiary: {
          DEFAULT: "var(--color-tertiary-500)",
          100: "var(--color-tertiary-100)",
          300: "var(--color-tertiary-300)",
          500: "var(--color-tertiary-500)",
          600: "var(--color-tertiary-600)",
          700: "var(--color-tertiary-700)",
          800: "var(--color-tertiary-800)",
        },
        success: {
          DEFAULT: "var(--color-success-500)",
          100: "var(--color-success-100)",
          300: "var(--color-success-300)",
          500: "var(--color-success-500)",
          600: "var(--color-success-600)",
          700: "var(--color-success-700)",
          800: "var(--color-success-800)",
        },
        danger: {
          DEFAULT: "var(--color-danger-500)",
          100: "var(--color-danger-100)",
          300: "var(--color-danger-300)",
          500: "var(--color-danger-500)",
          600: "var(--color-danger-600)",
          700: "var(--color-danger-700)",
          800: "var(--color-danger-800)",
        },
        tab: {
          DEFAULT: "var(--color-tab-300)",
          300: "var(--color-tab-300)",
          500: "var(--color-tab-500)",
        },
      },
    },
  },
  daisyui: {
    themes: [
      {
        nina: {
          primary: "#74A333",
          "primary-content": "#fff",
          secondary: "#004C6C",
          "secondary-light": "#004C6C",
          "secondary-content": "#fff",
          accent: "#E57200",
          neutral: "#425563",
          "base-100": "#ffffff",
        },
      },
    ],
  },
  plugins: [
    /**
     * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
     * for forms. If you don't like it or have own styling for forms,
     * comment the line below to disable '@tailwindcss/forms'.
     */
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
    require("daisyui"),
  ],
};
