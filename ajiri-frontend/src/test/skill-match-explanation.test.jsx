import { expect, it } from 'vitest'
import { render, screen } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import SkillMatchExplanation from '../components/SkillMatchExplanation'

function page(explanation) {
  return render(
    <MemoryRouter>
      <SkillMatchExplanation explanation={explanation} />
    </MemoryRouter>
  )
}
const explanation = {
  status: 'compared',
  matched_count: 1,
  required_count: 2,
  matched_skills: [{ id: 1, name: 'Python' }],
  missing_skills: [{ id: 2, name: 'SQL' }],
}
it('explains overlap with actionable profile correction and no qualification claim', () => {
  page(explanation)
  expect(screen.getByText(/Your profile lists 1 of the 2 skills/)).toBeVisible()
  expect(screen.getByText('Python')).toBeVisible()
  expect(screen.getByText('SQL')).toBeVisible()
  expect(screen.getByText(/does not mean you lack it/)).toBeVisible()
  expect(
    screen.getByText(/A lower score does not restrict browsing or applying/)
  ).toBeVisible()
  expect(
    screen.getByRole('link', { name: 'Review and edit my profile skills' })
  ).toHaveAttribute('href', '/profile')
})
it('distinguishes absent job skills from absent candidate skills', () => {
  const view = page({
    ...explanation,
    status: 'no_job_skills',
    matched_skills: [],
    missing_skills: [],
  })
  expect(screen.getByText(/no skill comparison yet/)).toBeVisible()
  view.unmount()
  page({ ...explanation, status: 'no_profile_skills', matched_skills: [] })
  expect(screen.getByText(/Add your skills to your profile/)).toBeVisible()
  expect(screen.queryByText('SQL')).not.toBeInTheDocument()
})
it('explains zero overlap and complete overlap without implying hiring outcomes', () => {
  const view = page({ ...explanation, matched_skills: [], matched_count: 0 })
  expect(screen.getByText('No listed skills overlap yet.')).toBeVisible()
  view.unmount()
  page({ ...explanation, missing_skills: [] })
  expect(screen.getByText(/All the role’s listed skills appear/)).toBeVisible()
  expect(
    screen.getByText(/does not assess qualifications or predict hiring/)
  ).toBeVisible()
})
it('renders no invented explanation when the API has none', () => {
  page(null)
  expect(screen.queryByRole('heading')).not.toBeInTheDocument()
})
