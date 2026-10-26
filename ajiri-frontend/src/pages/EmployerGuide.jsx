import { Link } from 'react-router-dom'
import { Button, Card } from '../components/ui'

export default function EmployerGuide() {
  return (
    <div className="stack page-stack">
      <section>
        <span className="eyebrow">FOR EMPLOYERS</span>
        <h1>Credible vacancies, reviewed before publication.</h1>
        <p className="lead">
          Prepare a clear job post with an explicit closing date. An independent
          staff review is required before it appears to job seekers.
        </p>
        <p>
          Employer onboarding is currently a pilot. A verified account email is
          required to submit; account verification is not yet available for
          every account.
        </p>
      </section>
      <Card className="stack">
        <h2>What you will need</h2>
        <ul className="stack list-disc pl-6">
          <li>Your organisation name and official website.</li>
          <li>A clear title, location, responsibilities and requirements.</li>
          <li>
            The official application destination and a future closing date and
            time.
          </li>
          <li>
            Authority to advertise the role, with no applicant registration,
            processing or application fees.
          </li>
        </ul>
      </Card>
      <Card className="stack">
        <h2>How review works</h2>
        <ol className="stack list-decimal pl-6">
          <li>
            Submit your organisation and vacancy from your signed-in workspace.
            Submission keeps the vacancy pending; it does not publish it.
          </li>
          <li>
            A staff reviewer checks the organisation, authority to advertise,
            official source and application destination, closing date and
            absence of applicant fees.
          </li>
          <li>
            The reviewer must be different from the submitting account. If an
            independent review cannot be completed, the vacancy stays
            unpublished.
          </li>
          <li>
            A decision records its reason, time and the reviewed revision.
            Changed information needs review again; no approval or review time
            is guaranteed.
          </li>
        </ol>
      </Card>
      <Card className="stack">
        <h2>After publication</h2>
        <p>
          Expired or stale vacancies leave active listings. Withdraw a role when
          it closes early. Existing application documents remain available to
          their owners.
        </p>
        <p>
          Review is a documented check, not a guarantee about an employer or a
          job. Job seekers never pay Ajiri to apply.
        </p>
        <Button asChild>
          <Link to="/employers">Open employer workspace</Link>
        </Button>
        <Link to="/">Back to Ajiri</Link>
      </Card>
    </div>
  )
}
