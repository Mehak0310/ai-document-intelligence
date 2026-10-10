import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const localPython = join(root, '.venv', process.platform === 'win32' ? 'Scripts' : 'bin', process.platform === 'win32' ? 'python.exe' : 'python');
const python = process.env.QA_PYTHON || (existsSync(localPython) ? localPython : 'python');

export default defineConfig({
  testDir: './tests/browser', workers: 1, fullyParallel: false, timeout: 30_000,
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    { command: `"${python}" -m uvicorn scripts.qa_server:app --host 127.0.0.1 --port 8010`, cwd: root, url: 'http://127.0.0.1:8010/health', reuseExistingServer: false, timeout: 60_000 },
    { command: 'npm run dev', url: 'http://127.0.0.1:5173', env: { VITE_API_URL: 'http://127.0.0.1:8010' }, reuseExistingServer: false, timeout: 60_000 },
  ],
});
