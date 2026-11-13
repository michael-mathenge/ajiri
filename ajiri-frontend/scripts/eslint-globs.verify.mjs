// see ../../ajiri-backend/docs/CONCEPTS.md#eslint-glob-security
import test from 'node:test'
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { mkdir, mkdtemp, writeFile, rm } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { ESLint } from 'eslint'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const eslint = new ESLint({ cwd: root })

test('ESLint and config-array both resolve a patched matcher', () => {
  const require = createRequire(import.meta.url)
  const fromESLint = createRequire(require.resolve('eslint'))
  const fromConfigArray = createRequire(
    fromESLint.resolve('@eslint/config-array')
  )
  for (const resolveFrom of [fromESLint, fromConfigArray]) {
    const { version } = resolveFrom('minimatch/package.json')
    const [major, minor, patch] = version.split('.').map(Number)
    assert.ok(major > 11 || (major === 11 && (minor > 0 || patch >= 1)))
  }
})

test('source globs keep selecting JS, JSX, modules and dotfiles for linting', async () => {
  // Exercise the real lint engine: matching a path must still catch a real defect.
  for (const name of [
    'src/example.js',
    'src/pages/Example.jsx',
    'src/deep/nested/example.mjs',
    'src/.hidden/example.js',
    'scripts/example.mjs',
    'eslint.config.js',
  ]) {
    const filePath = path.join(root, ...name.split('/'))
    assert.equal(await eslint.isPathIgnored(filePath), false, name)
    const [result] = await eslint.lintText("typeof value === 'strnig'", {
      filePath,
    })
    assert.ok(
      result.messages.some(({ ruleId }) => ruleId === 'valid-typeof'),
      name
    )
  }
  const [jsx] = await eslint.lintText('export const View = () => <main />', {
    filePath: path.join(root, 'src', 'pages', 'Example.jsx'),
  })
  assert.equal(jsx.errorCount, 0)
})

test('generated files, dependencies and unsupported extensions stay excluded', async () => {
  for (const name of [
    'dist/assets/example.js',
    'node_modules/example/index.js',
    'src/nested/node_modules/example/index.js',
    'src/example.json',
    'src/example.css',
  ]) {
    assert.equal(
      await eslint.isPathIgnored(path.join(root, ...name.split('/'))),
      true,
      name
    )
  }
})

test('lintFiles brace and globstar patterns find every intended fixture', async () => {
  const scratch = path.join(root, '.verification')
  await mkdir(scratch, { recursive: true })
  const temporary = await mkdtemp(path.join(scratch, 'eslint-globs-'))
  try {
    await mkdir(path.join(temporary, 'nested'))
    const files = ['one.js', 'nested/two.jsx', 'nested/three.mjs']
    for (const name of files) {
      await writeFile(
        path.join(temporary, ...name.split('/')),
        "typeof value === 'strnig'"
      )
    }
    await writeFile(path.join(temporary, 'notes.txt'), 'not JavaScript')
    const pattern = path.relative(root, temporary).split(path.sep).join('/')
    const results = await eslint.lintFiles([`${pattern}/**/*.{js,jsx,mjs}`])
    assert.equal(results.length, files.length)
    for (const result of results) {
      assert.ok(result.messages.some(({ ruleId }) => ruleId === 'valid-typeof'))
    }
  } finally {
    assert.ok(temporary.startsWith(scratch + path.sep))
    await rm(temporary, { recursive: true })
  }
})
