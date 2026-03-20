// global-setup.js - DB reset is handled by webServer command in playwright.config.js
export default async function globalSetup() {
  console.log('[global-setup] DB setup is handled by webServer startup command.');
}
