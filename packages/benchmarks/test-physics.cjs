#!/usr/bin/env node
/**
 * Test physics validation against both implementations
 */

const fs = require('fs');
const path = require('path');

const popkitFile = process.argv[2] || 'results/bouncing-balls-popkit-1765801033560/balls.js';
const vanillaFile = process.argv[3] || 'results/bouncing-balls-vanilla-1765775996133/balls.js';

function testPhysics(filePath) {
  const code = fs.readFileSync(filePath, 'utf8');

  // Test 1: Excessive damping
  const hasDamping = /(DAMPING|FRICTION)\s*=\s*0\.[0-9]+/.test(code);
  const appliesEveryFrame = /(this\.v[xy]|v[xy])\s*\*=\s*(DAMPING|FRICTION)/.test(code);
  const conditionalApplication = /if.*collision|if.*wall|if.*bounce/.test(code);
  const excessiveDamping = hasDamping && appliesEveryFrame && !conditionalApplication;

  // Test 2: Gravity vertical only
  const gravityCorrect = /this\.vy\s*\+=\s*GRAVITY|vy\s*\+=\s*GRAVITY|vy\s*\+=\s*gravity/.test(code);
  const gravityWrong = /this\.vx\s*\+=\s*GRAVITY|vx\s*\+=\s*GRAVITY|vx\s*\+=\s*gravity/.test(code);

  // Test 3: Wall bounce reflection
  const hasReflection = /v[xy]\s*\*=\s*-|v[xy]\s*=\s*-v[xy]/.test(code) || /Math\.abs/.test(code);

  return {
    excessiveDamping: excessiveDamping ? 'FAIL' : 'PASS',
    gravityVertical: (gravityCorrect && !gravityWrong) ? 'PASS' : 'FAIL',
    wallReflection: hasReflection ? 'PASS' : 'FAIL',
    overallPass: !excessiveDamping && gravityCorrect && !gravityWrong && hasReflection
  };
}

console.log('Testing physics validation...\n');

console.log('PopKit Implementation:');
const popkitResults = testPhysics(popkitFile);
console.log(`  Excessive Damping:  ${popkitResults.excessiveDamping}`);
console.log(`  Gravity Vertical:   ${popkitResults.gravityVertical}`);
console.log(`  Wall Reflection:    ${popkitResults.wallReflection}`);
console.log(`  Overall:            ${popkitResults.overallPass ? 'PASS' : 'FAIL'}`);

console.log('\nVanilla Implementation:');
const vanillaResults = testPhysics(vanillaFile);
console.log(`  Excessive Damping:  ${vanillaResults.excessiveDamping}`);
console.log(`  Gravity Vertical:   ${vanillaResults.gravityVertical}`);
console.log(`  Wall Reflection:    ${vanillaResults.wallReflection}`);
console.log(`  Overall:            ${vanillaResults.overallPass ? 'PASS' : 'FAIL'}`);

console.log('\n' + '='.repeat(60));
console.log('Verdict:');
if (popkitResults.overallPass && !vanillaResults.overallPass) {
  console.log('✓ PopKit is BETTER');
} else if (!popkitResults.overallPass && vanillaResults.overallPass) {
  console.log('✗ Vanilla is BETTER');
} else if (popkitResults.overallPass && vanillaResults.overallPass) {
  console.log('= Both PASS quality tests');
} else {
  console.log('= Both FAIL quality tests');
}
console.log('='.repeat(60));

// Exit with non-zero if PopKit failed
process.exit(popkitResults.overallPass ? 0 : 1);
