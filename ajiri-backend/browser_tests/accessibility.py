"""Sanitized axe results for synthetic, isolated browser journeys only.

see docs/CONCEPTS.md#accessibility-performance-budgets
"""
import json
import os
from pathlib import Path
from django.conf import settings


def tools_root():
    return Path(os.environ.get('AJIRI_FRONTEND_TOOLS', settings.BASE_DIR.parent / 'ajiri-frontend'))


def audit(case, page, label):
    source = tools_root() / 'node_modules' / 'axe-core' / 'axe.min.js'
    case.assertTrue(source.is_file(), 'Run the locked frontend installation before accessibility checks.')
    page.add_script_tag(path=str(source))
    result = page.evaluate("""async () => {
      const result = await axe.run(document, {runOnly: {type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice']}});
      return {violations: result.violations.map(rule => ({id: rule.id, impact: rule.impact,
        targets: rule.nodes.map(node => node.target)})),
        incomplete: result.incomplete.map(rule => rule.id)};
    }""")
    output = settings.BASE_DIR.parent / '.verification' / 'accessibility'
    output.mkdir(parents=True, exist_ok=True)
    records = getattr(case, '_axe_records', [])
    records.append({'page': label, **result})
    case._axe_records = records
    (output / (case._testMethodName + '.json')).write_text(json.dumps(records, indent=2), encoding='utf-8')
    # No blanket exemptions: all detected violations block. Incomplete checks
    # remain visible for manual review, never represented as automated passes.
    case.assertEqual(result['violations'], [], f'Accessibility violations on {label}: {result["violations"]}')
