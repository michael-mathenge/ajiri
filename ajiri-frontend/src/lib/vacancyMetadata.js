// One vocabulary for employer input, search and saved preferences.
// see docs/CONCEPTS.md#normalized-vacancy-filters
import metadata from '../../../ajiri-backend/jobs/vacancy_metadata.json'

export const counties = metadata.counties
export const workArrangements = metadata.work_arrangements
export const maxExperienceYears = metadata.max_experience_years
export function normalizeVacancyValues(values, employer = false) {
  const experience = employer ? 'min_experience_years' : 'max_experience_years'
  return {
    ...values,
    county: values.county || null,
    work_arrangement: values.work_arrangement || null,
    [experience]:
      values[experience] === '' || values[experience] == null
        ? null
        : Number(values[experience]),
  }
}
export const countyLabel = (value) =>
  counties.find(([key]) => key === value)?.[1] || 'Not stated'
export const workArrangementLabel = (value) =>
  workArrangements.find(([key]) => key === value)?.[1] || 'Not stated'
