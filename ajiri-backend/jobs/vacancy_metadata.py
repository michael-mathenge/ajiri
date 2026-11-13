"""Explicit employer facts; never infer county, remote work or experience from prose."""
import json
from pathlib import Path

# see docs/CONCEPTS.md#normalized-vacancy-filters
# County names: https://kdsp.devolution.go.ke/counties
METADATA = json.loads(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))
COUNTIES = METADATA['counties']
WORK_ARRANGEMENTS = METADATA['work_arrangements']
MAX_EXPERIENCE_YEARS = METADATA['max_experience_years']
