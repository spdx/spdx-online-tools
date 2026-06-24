module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["airbnb-base"],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: "module",
  },
  rules: {
    "max-len": ["warn", { code: 120 }], // Limit lines to 120 characters
    indent: ["warn", 2], // Use 2 spaces for indentation
    "no-tabs": "warn", // Disallow tabs
    "linebreak-style": ["warn", "unix"], // Enforce Unix line endings
    "no-unused-vars": ["warn", { argsIgnorePattern: "^_" }], // Ignore unused function arguments starting with underscore (_)
    "no-console": "off", // Allow console statements
    "comma-dangle": ["warn", "never"], // Disallow trailing commas in arrays and objects
    "arrow-parens": ["warn", "as-needed"], // Require parentheses around arrow function parameters only when needed
    "object-curly-spacing": ["warn", "always"], // Require spaces inside curly braces of objects
    quotes: ["warn", "double", { avoidEscape: true }],
  },
};
