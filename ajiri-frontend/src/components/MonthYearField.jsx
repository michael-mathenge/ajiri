import { Input } from './ui'

const months = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
]

// Keep partial input in the draft so it cannot silently disappear on save.
// see docs/CONCEPTS.md#cv-builder-flow
export default function MonthYearField({
  id,
  label,
  value = '',
  onChange,
  disabled = false,
  errorId,
}) {
  const [year = '', month = ''] = value.split('-')
  const change = (nextYear, nextMonth) =>
    onChange(nextYear || nextMonth ? `${nextYear}-${nextMonth}` : '')
  return (
    <fieldset className="field" disabled={disabled}>
      <legend>{label}</legend>
      <div className="profile-grid">
        <div className="field">
          <label htmlFor={`${id}-month`}>Month</label>
          <select
            id={`${id}-month`}
            className="input"
            aria-label={`${label} — month`}
            aria-invalid={Boolean(errorId)}
            aria-describedby={errorId}
            value={month}
            required={Boolean(year)}
            onChange={(e) => change(year, e.target.value)}
          >
            <option value="">Choose month</option>
            {months.map((name, index) => (
              <option key={name} value={String(index + 1).padStart(2, '0')}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${id}-year`}>Year</label>
          <Input
            id={`${id}-year`}
            type="number"
            inputMode="numeric"
            min="1"
            max="9999"
            step="1"
            aria-invalid={Boolean(errorId)}
            aria-describedby={errorId}
            placeholder="YYYY"
            aria-label={`${label} — year`}
            value={year}
            required={Boolean(month)}
            onChange={(e) => change(e.target.value, month)}
          />
        </div>
      </div>
      <button
        type="button"
        className="btn btn-outline"
        disabled={disabled || !value}
        onClick={() => onChange('')}
      >
        Clear {label.toLowerCase()}
      </button>
      {disabled && <p className="muted">Present — no end date needed.</p>}
    </fieldset>
  )
}
