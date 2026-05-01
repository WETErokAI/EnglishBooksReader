@echo off
set NODE_OPTIONS=--max-old-space-size=4096
cd /d "%~dp0"
npx vitest run tests/unit/test_useChunkLoader.test.tsx
