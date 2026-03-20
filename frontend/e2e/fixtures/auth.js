import { test as base, expect } from '@playwright/test';

const API_URL = 'http://127.0.0.1:8000/api/auth/login';
const APP_URL = 'http://localhost:3000';

const USERS = {
  admin: { username: 'admin', password: 'Admin123' },
  staff: { username: 'tanaka', password: 'Tanaka123' },
  viewer: { username: 'sato', password: 'Sato12345' },
};

async function authenticate(browser, { username, password }) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error(`Authentication failed for ${username}: ${response.status} ${await response.text()}`);
  }

  const body = await response.json();
  const token = body.data.access_token;

  const context = await browser.newContext();
  await context.addInitScript(
    (t) => {
      sessionStorage.setItem('access_token', t);
    },
    token,
  );

  const page = await context.newPage();
  await page.goto(APP_URL);
  await page.waitForLoadState('load');

  return { context, page };
}

async function createFixture(browser, role) {
  const { context, page } = await authenticate(browser, USERS[role]);
  return { context, page };
}

const test = base.extend({
  adminContext: async ({ browser }, use) => {
    const { context } = await createFixture(browser, 'admin');
    await use(context);
    await context.close();
  },
  adminPage: async ({ browser }, use) => {
    const { context, page } = await createFixture(browser, 'admin');
    await use(page);
    await context.close();
  },
  staffContext: async ({ browser }, use) => {
    const { context } = await createFixture(browser, 'staff');
    await use(context);
    await context.close();
  },
  staffPage: async ({ browser }, use) => {
    const { context, page } = await createFixture(browser, 'staff');
    await use(page);
    await context.close();
  },
  viewerContext: async ({ browser }, use) => {
    const { context } = await createFixture(browser, 'viewer');
    await use(context);
    await context.close();
  },
  viewerPage: async ({ browser }, use) => {
    const { context, page } = await createFixture(browser, 'viewer');
    await use(page);
    await context.close();
  },
});

export { test, expect };
