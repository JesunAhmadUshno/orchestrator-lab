import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
// The site reads ../level-*/ results, scenario, code and READMEs at build time,
// so every number on the page is generated, never typed.
const sha = (p) => createHash('sha256').update(readFileSync(new URL(p, import.meta.url))).digest('hex');
export default defineConfig({
  base: '/orchestrator-lab/',
  plugins: [react()],
  server: { fs: { allow: ['..'] } },
  define: {
    __SHA256__: JSON.stringify({
      'level-1-learn/results_learn.json': sha('../level-1-learn/results_learn.json'),
      'level-2-build/results_build.json': sha('../level-2-build/results_build.json'),
      'level-3-deep/results_deep.json': sha('../level-3-deep/results_deep.json'),
      'level-3-deep/results_sweep.json': sha('../level-3-deep/results_sweep.json'),
    }),
  },
});
