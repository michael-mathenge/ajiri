// see ../../ajiri-backend/docs/CONCEPTS.md#incremental-quality
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { ESLint } from 'eslint'
import * as prettier from 'prettier'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const [mode, ...names] = process.argv.slice(2)
const files = names.map((name) => path.resolve(name))
if (!['lint', 'format'].includes(mode) || !files.length) {
  console.error('Usage: node check-files.mjs lint|format FILE...')
  process.exit(2)
}
if (process.versions.node.split('.').slice(0, 2).join('.') !== '24.19') {
  console.error('Use the documented Node 24.19 runtime.')
  process.exit(2)
}
if (files.some((file) => !file.startsWith(root + path.sep))) {
  console.error('Only frontend source/configuration files are accepted.')
  process.exit(2)
}
if (mode === 'lint') {
  const eslint = new ESLint({ cwd: root })
  const results = await eslint.lintFiles(files)
  console.log(await (await eslint.loadFormatter('stylish')).format(results))
  process.exitCode = results.some(
    (result) => result.errorCount || result.warningCount
  )
    ? 1
    : 0
} else {
  for (const file of files) {
    const source = await readFile(file, 'utf8')
    const options = { ...(await prettier.resolveConfig(file)), filepath: file }
    if (!(await prettier.check(source, options))) {
      console.error(`Formatting needed: ${path.relative(root, file)}`)
      process.exitCode = 1
    }
  }
}
