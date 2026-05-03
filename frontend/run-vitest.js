process.env.NODE_OPTIONS = '--max-old-space-size=4096';
const { execSync } = require('child_process');
execSync('npx vitest run tests/unit/test_useChunkLoader.test.tsx', { stdio: 'inherit' });
