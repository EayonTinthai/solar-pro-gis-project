import path from 'path';
import { fileURLToPath } from 'url';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const hasClerk = Boolean(env.VITE_CLERK_PUBLISHABLE_KEY);

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        // Mock Clerk when no publishable key is configured
        ...(!hasClerk && {
          '@clerk/react': path.resolve(__dirname, './src/lib/clerk-mock.js'),
        }),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
    },
  };
});
