import Dialog from '../components/Dialog'
import { useEffect } from 'react'
import { useSchemaForm } from '../hooks/useSchemaForm'
import { searchSchema } from '../lib/formSchemas'
import FormErrors from '../components/FormErrors'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  ArrowRight,
  BriefcaseBusiness,
  MapPin,
  Search,
  SlidersHorizontal,
} from 'lucide-react'
import { useApiQuery } from '../hooks/useApiQuery'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Input,
  LoadingState,
  MatchScore,
  Pagination,
  Select,
} from '../components/ui'
import { dateLabel, jobType, salaryLabel } from '../lib/utils'

function Filters({ register }) {
  return (
    <>
      <div className="field">
        <label htmlFor="search-title">Job title</label>
        <Input
          id="search-title"
          name="title"
          placeholder="e.g. Software developer"
          {...register('title')}
        />
      </div>
      <div className="field">
        <label htmlFor="search-location">Location</label>
        <Input
          id="search-location"
          name="location"
          placeholder="e.g. Nairobi"
          {...register('location')}
        />
      </div>
      <div className="field">
        <label htmlFor="search-type">Job type</label>
        <Select id="search-type" {...register('job_type')}>
          <option value="">All job types</option>
          <option value="full_time">Full time</option>
          <option value="part_time">Part time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
        </Select>
      </div>
    </>
  )
}
export default function JobList() {
  // URL state makes filters shareable and preserves them with browser Back.
  // see docs/CONCEPTS.md#url-search-state
  const [params, setParams] = useSearchParams()
  const title = params.get('title') || ''
  const location = params.get('location') || ''
  const type = params.get('job_type') || ''
  const {
    form,
    errors: filterErrors,
    submit: validateSubmit,
  } = useSchemaForm(searchSchema, { title, location, job_type: type })
  const { reset } = form
  useEffect(() => {
    reset({ title, location, job_type: type })
  }, [title, location, type, reset])
  const requestedPage = Number(params.get('page'))
  const page =
    Number.isSafeInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
  const query = new URLSearchParams({ page: String(page) })
  if (title) query.set('title', title)
  if (location) query.set('location', location)
  if (type) query.set('job_type', type)
  const { data, loading, error, retry } = useApiQuery(`/jobs/?${query}`)
  const { data: profile } = useApiQuery('/profiles/me/')
  // Missing profile data is unknown, not evidence of an empty skills list.
  // see docs/CONCEPTS.md#ui-feedback
  const hasSkills = Array.isArray(profile?.skills)
    ? profile.skills.length > 0
    : null
  const [showFilters, setShowFilters] = useState(false)
  const filtered = Boolean(title || location || type)
  const submit = (values) => {
    const next = new URLSearchParams()
    for (const [key, value] of Object.entries(values))
      if (value.trim()) next.set(key, value.trim())
    setParams(next)
  }
  const changePage = (next) => {
    const updated = new URLSearchParams(params)
    updated.set('page', String(next))
    setParams(updated)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }
  return (
    <div className="stack page-stack">
      <section className="page-heading">
        <div>
          <span className="eyebrow">OPPORTUNITIES, WITH YOU IN MIND</span>
          <h1>Find your next chapter.</h1>
          <p className="lead">
            Explore jobs across Kenya. Start with the skills that make you, you.
          </p>
        </div>
        <span className="heading-icon">
          <BriefcaseBusiness size={36} aria-hidden="true" />
        </span>
      </section>
      <Card className="search-card">
        <form
          noValidate
          onSubmit={validateSubmit(submit)}
          key={`${title}|${location}|${type}`}
        >
          <div className={`search-fields ${showFilters ? 'filters-open' : ''}`}>
            <Filters register={form.register} />
            <Button type="submit">
              <Search size={18} aria-hidden="true" />
              Search jobs
            </Button>
          </div>
          <FormErrors errors={filterErrors} prefix="filters" />
          <div className="filter-tools">
            <Button
              variant="ghost"
              className="filter-toggle"
              aria-expanded={showFilters}
              onClick={() => setShowFilters(!showFilters)}
            >
              <SlidersHorizontal size={16} aria-hidden="true" />
              {showFilters ? 'Fewer filters' : 'Location & job type'}
            </Button>
            {filtered && (
              <Button variant="ghost" onClick={() => setParams({})}>
                Clear filters
              </Button>
            )}
          </div>
        </form>
      </Card>
      <div className="results-heading">
        <h2>
          {loading
            ? 'Finding opportunities…'
            : error
              ? 'Job opportunities'
              : `${data?.count ?? 0} ${(data?.count ?? 0) === 1 ? 'opportunity' : 'opportunities'}`}
        </h2>
        <Dialog
          trigger={<Button variant="ghost">How matching works</Button>}
          title="Your skills, matched to the role"
          description="The match score compares your profile’s skills with the skills listed for a job."
        >
          <p>
            A score of 70% or more is a strong skill match and can trigger a job
            alert. A lower score does not stop you applying.
          </p>
          <p className="muted mt-4">
            A 0% score can also mean that no skills are listed for a job. Scores
            describe skill overlap, not your chances of being hired.
          </p>
        </Dialog>
      </div>
      {loading ? (
        <LoadingState label="Loading jobs" />
      ) : error ? (
        <ErrorState onRetry={retry}>{error}</ErrorState>
      ) : !data.results.length ? (
        <EmptyState
          title={
            filtered ? 'No jobs match those filters' : 'No opportunities yet'
          }
          action={
            filtered && (
              <Button variant="outline" onClick={() => setParams({})}>
                Clear filters
              </Button>
            )
          }
        >
          {filtered
            ? 'Try a broader title or another location.'
            : 'Check back soon for new job listings.'}
        </EmptyState>
      ) : (
        <>
          <div className="job-grid">
            {data.results.map((job) => (
              <Card className="job-card" key={job.id}>
                <div className="job-card-top">
                  <span className="company-avatar" aria-hidden="true">
                    {job.company_name.slice(0, 2).toUpperCase()}
                  </span>
                  {hasSkills === false ? (
                    <Link to="/profile" className="inline-link text-sm">
                      Add skills to see matches
                    </Link>
                  ) : hasSkills === true ? (
                    <MatchScore score={job.match_score} />
                  ) : null}
                </div>
                <p className="company-name">{job.company_name}</p>
                <h3>
                  <Link to={`/jobs/${job.id}`}>{job.title}</Link>
                </h3>
                <p className="icon-text muted">
                  <MapPin size={16} aria-hidden="true" />
                  {job.location || 'Location not listed'}
                </p>
                <div className="job-tags">
                  <Badge className="capitalize">{jobType(job.job_type)}</Badge>
                </div>
                <p className="salary">{salaryLabel(job)}</p>
                <div className="job-card-bottom">
                  <span className="muted text-sm">
                    Posted {dateLabel(job.posted_at)}
                  </span>
                  <Link
                    to={`/jobs/${job.id}`}
                    className="inline-link"
                    aria-label={`View job: ${job.title} at ${job.company_name}`}
                  >
                    View job
                    <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                </div>
              </Card>
            ))}
          </div>
          <Pagination
            page={page}
            hasNext={Boolean(data.next)}
            hasPrevious={Boolean(data.previous)}
            onChange={changePage}
          />
        </>
      )}
      <p className="safety-note">
        A good opportunity should never ask you to pay to apply. Check employer
        details before sharing personal information.
      </p>
    </div>
  )
}
