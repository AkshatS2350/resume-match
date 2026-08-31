module.exports = {
  extends: ["next/core-web-vitals"],
  rules: {
    "no-restricted-imports": [
      "error",
      {
        patterns: [
          {
            group: ["../generated", "../generated/*"],
            message: "API types must be consumed from src/lib/api/generated."
          }
        ]
      }
    ]
  }
};
