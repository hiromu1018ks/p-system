import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './specs',

  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },

  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  workers: 1,

  reporter: [['html', { open: 'never' }]],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  globalSetup: './global-setup.js',

  webServer: [
    {
      name: 'backend',
      command:
        'cd /home/hart/Code/p-system/backend && source venv/bin/activate && rm -f test_zaisan.db test_zaisan.db-wal test_zaisan.db-shm && DATABASE_URL=sqlite:///./test_zaisan.db alembic upgrade head && DATABASE_URL=sqlite:///./test_zaisan.db python seed.py && DATABASE_URL=sqlite:///./test_zaisan.db uvicorn main:app --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      name: 'frontend',
      command: 'npm run dev',
      cwd: '/home/hart/Code/p-system/frontend',
      url: 'http://localhost:3000',
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
