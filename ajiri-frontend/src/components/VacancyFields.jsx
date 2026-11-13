import { Input, Select } from './ui'
import {
  counties,
  workArrangements,
  maxExperienceYears,
} from '../lib/vacancyMetadata'

// see docs/CONCEPTS.md#normalized-vacancy-filters
export default function VacancyFields({
  register,
  defaults = {},
  employer = false,
  prefix,
  errors = {},
}) {
  const experience = employer ? 'min_experience_years' : 'max_experience_years'
  const props = (name) => ({
    ...(register
      ? register(name)
      : { name, defaultValue: defaults[name] ?? '' }),
    id: `${prefix}-${name}`,
    'aria-invalid': Boolean(errors[name]),
    'aria-describedby': errors[name] ? `${prefix}-${name}-error` : undefined,
  })
  return (
    <>
      <div className="field">
        <label htmlFor={`${prefix}-county`}>County</label>
        <Select {...props('county')}>
          <option value="">
            {employer
              ? 'Not stated / outside Kenya'
              : 'All counties, including unstated'}
          </option>
          {counties.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
      </div>
      <div className="field">
        <label htmlFor={`${prefix}-work_arrangement`}>Work arrangement</label>
        <Select {...props('work_arrangement')}>
          <option value="">
            {employer ? 'Not stated' : 'All arrangements, including unstated'}
          </option>
          {workArrangements.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
      </div>
      <div className="field">
        <label htmlFor={`${prefix}-${experience}`}>
          {employer
            ? 'Minimum required experience (years)'
            : 'Maximum required experience (years)'}
        </label>
        <Input
          type="number"
          min="0"
          max={maxExperienceYears}
          step="1"
          inputMode="numeric"
          {...props(experience)}
        />
        <p className="muted">
          {employer
            ? 'Leave blank when the requirement is not stated. Enter 0 only when no prior experience is required.'
            : 'Leave blank for any experience requirement. A chosen limit includes only roles with a stated requirement; 0 includes roles requiring no prior experience.'}
        </p>
      </div>
    </>
  )
}
