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
    "max-len": ["error", { code: 120 }], // Limit lines to 120 characters
    indent: ["error", 2], // Use 2 spaces for indentation
    "no-tabs": "error", // Disallow tabs
    "linebreak-style": ["error", "unix"], // Enforce Unix line endings
    "no-unused-vars": ["error", { argsIgnorePattern: "^_" }], // Ignore unused function arguments starting with underscore (_)
    "no-console": "off", // Allow console statements
    "comma-dangle": ["error", "never"], // Disallow trailing commas in arrays and objects
    "arrow-parens": ["error", "as-needed"], // Require parentheses around arrow function parameters only when needed
    "object-curly-spacing": ["error", "always"], // Require spaces inside curly braces of objects
    quotes: ["error", "double", { avoidEscape: true }],
  },
};
