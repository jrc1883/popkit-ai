/**
 * E2B Proof of Concept for PopKit Benchmarks
 *
 * Demonstrates basic E2B sandbox operations:
 * - Creating a sandbox
 * - Writing files
 * - Running code
 * - Extracting results
 *
 * Prerequisites:
 * 1. Get API key from https://e2b.dev/dashboard
 * 2. Set E2B_API_KEY environment variable
 * 3. Run: npx tsx packages/benchmarks/src/e2b/poc.ts
 */

// Note: E2B SDK must be installed to run this
// npm install @e2b/code-interpreter

async function runPOC() {
  // Dynamic import to avoid requiring E2B for basic usage
  const { Sandbox } = await import('@e2b/code-interpreter');

  console.log('='.repeat(60));
  console.log('E2B Sandbox Proof of Concept');
  console.log('='.repeat(60));

  // Check for API key
  if (!process.env.E2B_API_KEY) {
    console.error('\nError: E2B_API_KEY environment variable not set');
    console.error('Get your API key from https://e2b.dev/dashboard');
    console.error('Run: E2B_API_KEY=e2b_xxx npx tsx packages/benchmarks/src/e2b/poc.ts');
    process.exit(1);
  }

  console.log('\n1. Creating sandbox...');
  const startTime = Date.now();
  const sbx = await Sandbox.create({ timeout: 300 });
  console.log(`   Sandbox created in ${Date.now() - startTime}ms`);

  try {
    // Test 1: File System Operations
    console.log('\n2. Testing file system operations...');

    const testCode = `
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Test the function
const results = [];
for (let i = 0; i < 10; i++) {
  results.push(fibonacci(i));
}

console.log('Fibonacci sequence (first 10):', results.join(', '));
console.log('fibonacci(10) =', fibonacci(10));
console.log('TEST_PASSED:', results[9] === 34);
`;

    await sbx.files.write('/task/fibonacci.js', testCode);
    console.log('   File written: /task/fibonacci.js');

    // Test 2: List files
    const files = await sbx.files.list('/task');
    console.log(`   Files in /task: ${files.map((f: { name: string }) => f.name).join(', ')}`);

    // Test 3: Execute code
    console.log('\n3. Executing code...');
    const execStart = Date.now();
    const result = await sbx.commands.run('node /task/fibonacci.js');
    const execTime = Date.now() - execStart;

    console.log(`   Execution time: ${execTime}ms`);
    console.log(`   Exit code: ${result.exitCode}`);
    console.log('   Output:');
    result.stdout.split('\n').forEach((line: string) => {
      if (line.trim()) console.log(`     ${line}`);
    });

    // Test 4: Run npm commands
    console.log('\n4. Testing npm installation...');
    const npmResult = await sbx.commands.run('npm --version');
    console.log(`   npm version: ${npmResult.stdout.trim()}`);

    // Test 5: Python execution (Code Interpreter default)
    console.log('\n5. Testing Python execution...');
    const pyResult = await sbx.runCode(`
import sys
print(f"Python version: {sys.version.split()[0]}")
result = sum(range(1, 101))
print(f"Sum of 1-100: {result}")
`);
    console.log('   Python output:');
    pyResult.logs.stdout.forEach((line: string) => {
      console.log(`     ${line}`);
    });

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('POC Results Summary');
    console.log('='.repeat(60));
    console.log(`✓ Sandbox creation: ${Date.now() - startTime}ms total`);
    console.log(`✓ File operations: Working`);
    console.log(`✓ Node.js execution: ${execTime}ms`);
    console.log(`✓ Python execution: Working`);
    console.log(`✓ Exit code: ${result.exitCode}`);
    console.log(`✓ Test passed: ${result.stdout.includes('TEST_PASSED: true')}`);

  } catch (error) {
    console.error('\nError during POC:', error);
    throw error;
  } finally {
    console.log('\n6. Closing sandbox...');
    await sbx.close();
    console.log('   Sandbox closed successfully.');
    console.log('\nTotal time:', Date.now() - startTime, 'ms');
  }
}

// Run if called directly
runPOC().catch((error) => {
  console.error('POC failed:', error);
  process.exit(1);
});
