import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises'
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const command = path.join(root, 'scripts/check-files.mjs')
const run = (mode, file) =>
  spawnSync(process.execPath, [command, mode, file], {
    cwd: root,
    encoding: 'utf8',
  })

test('hooks reject outside paths and detect defects without rewriting files', async () => {
  const scratch = path.join(root, '.verification')
  await mkdir(scratch, { recursive: true })
  const temporary = await mkdtemp(path.join(scratch, 'quality-'))
  try {
    const valid = path.join(temporary, 'valid.js')
    const invalid = path.join(temporary, 'invalid.js')
    const unformatted = path.join(temporary, 'unformatted.js')
    await writeFile(valid, 'export const value = 1\n')
    await writeFile(invalid, 'const = 1\n')
    await writeFile(unformatted, 'export const value=1\n')
    assert.equal(run('lint', valid).status, 0)
    assert.equal(run('lint', invalid).status, 1)
    assert.equal(run('format', valid).status, 0)
    assert.equal(run('format', unformatted).status, 1)
    assert.equal(run('lint', path.join(root, '..', 'outside.js')).status, 2)
    const { readFile } = await import('node:fs/promises')
    assert.equal(await readFile(unformatted, 'utf8'), 'export const value=1\n')
  } finally {
    assert.ok(temporary.startsWith(scratch + path.sep))
    await rm(temporary, { recursive: true })
  }
})
