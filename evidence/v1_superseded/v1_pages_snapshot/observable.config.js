import { defineConfig } from "@observablehq/framework";

export default defineConfig({
  title: "Keystroke Observatory",
  root: "src",
  pages: [
    "pages/index.md",
    "pages/participants.md",
    "pages/sessions.md"
  ],
  theme: "observable",
  sidebar: true,
  public: "../public"
});