import { runTests } from '@vscode/test-electron';

async function main() {
  try {
    await runTests({
      extensionDevelopmentPath: __dirname + '/../', // or path to your extension
      extensionTestsPath: __dirname + '/extension.test.js', // compiled test file
    });
  } catch (err) {
    console.error('Failed to run tests');
    process.exit(1);
  }
}

main();
