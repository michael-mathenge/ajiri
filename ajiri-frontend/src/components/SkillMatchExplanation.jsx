import { Link } from 'react-router-dom'
import { Badge, Card } from './ui'

export default function SkillMatchExplanation({ explanation }) {
  // see docs/CONCEPTS.md#explainable-skill-matching
  if (!explanation) return null
  return (
    <Card>
      <h2>How your skills match</h2>
      {explanation.status === 'no_job_skills' ? (
        <p>
          No skills are listed for this role, so there is no skill comparison
          yet.
        </p>
      ) : explanation.status === 'no_profile_skills' ? (
        <p>Add your skills to your profile to compare them with this role.</p>
      ) : (
        <>
          <p>
            Your profile lists {explanation.matched_count} of the{' '}
            {explanation.required_count} skills listed for this role.
          </p>
          <h3>Skills in your profile</h3>
          {explanation.matched_skills.length ? (
            <ul className="job-tags">
              {explanation.matched_skills.map((skill) => (
                <li key={skill.id}>
                  <Badge>{skill.name}</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p>No listed skills overlap yet.</p>
          )}
          <h3>Skills not listed in your profile</h3>
          {explanation.missing_skills.length ? (
            <ul className="job-tags">
              {explanation.missing_skills.map((skill) => (
                <li key={skill.id}>
                  <Badge>{skill.name}</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p>All the role’s listed skills appear in your profile.</p>
          )}
        </>
      )}
      <p>
        This compares saved skill labels only. A skill missing from your profile
        does not mean you lack it. It does not assess qualifications or predict
        hiring.
      </p>
      <p>
        The 70% threshold only controls match alerts. A lower score does not
        restrict browsing or applying to an eligible job. Skill overlap does not
        verify that a vacancy is open.
      </p>
      <Link to="/profile">Review and edit my profile skills</Link>
    </Card>
  )
}
