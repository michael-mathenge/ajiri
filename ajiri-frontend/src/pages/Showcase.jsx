import { Link } from 'react-router-dom'
import { Button, Card } from '../components/ui'

// Public introduction only: no account, document or job API is requested here.
// see docs/CONCEPTS.md#public-showcase-journey
export default function Showcase() {
  return (
    <div className="stack page-stack">
      <section className="stack">
        <span className="eyebrow">AJIRI KENYA · EARLY ACCESS</span>
        <h1>Build your CV. Prepare your next application.</h1>
        <p className="lead">
          Turn your own information into a CV, check every detail and download
          the version you approve. Take the next step at your own pace.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to="/register">Create a free account</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/login">Log in to Ajiri</Link>
          </Button>
        </div>
        <p className="muted">No payment details needed. No application fee.</p>
      </section>
      <div className="plans-grid">
        <Card>
          <h2>A CV you control</h2>
          <p>
            Add your experience, education and skills. Review the draft, approve
            it yourself and download your CV as a Word document.
          </p>
        </Card>
        <Card>
          <h2>Current vacancies only</h2>
          <p>
            Jobs without current availability evidence stay hidden. An old feed
            entry is not presented as a newly verified opportunity.
          </p>
        </Card>
        <Card>
          <h2>Free to apply</h2>
          <p>
            Ajiri does not charge job seekers to browse or apply. Paid plans are
            previews; no subscription starts when you create an account.
          </p>
        </Card>
      </div>
      <Card className="stack">
        <h2>Start with your CV</h2>
        <ol className="stack list-decimal pl-6">
          <li>
            Create an account and read the privacy notice before agreeing.
          </li>
          <li>
            Save your profile, then open CV builder and enter your information.
          </li>
          <li>
            Save and preview, approve the exact revision, then download it.
          </li>
        </ol>
        <p>
          Your profile and documents stay private to your account. Creating a CV
          does not submit a job application or give permission to send email.
        </p>
      </Card>
      <Card className="stack">
        <h2>What to expect in early access</h2>
        <p>
          CV building is available after registration. You can build your CV
          without requesting an email verification link.
        </p>
        <p>
          Vacancies depend on current evidence; there may be no active jobs to
          show. Application preparation also needs an eligible vacancy and a
          verified email.
        </p>
        <p>
          Account email delivery and employer onboarding are being piloted.
          Verification may not yet be available for every account. Application
          email delivery is not generally enabled; employer website submissions
          remain your action.
        </p>
        <p>No job, interview or employment outcome is guaranteed.</p>
        <Link to="/employer-guide">How employer review works</Link>
      </Card>
    </div>
  )
}
