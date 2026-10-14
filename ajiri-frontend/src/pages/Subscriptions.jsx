import { Link } from 'react-router-dom'
import { Badge, Button, Card } from '../components/ui'

const plans = [
  {
    name: 'Free',
    price: 0,
    description: 'Start exploring opportunities with Ajiri.',
  },
  {
    name: 'Starter',
    price: 499,
    description: 'A planned upgrade for your job search.',
  },
  {
    name: 'Pro',
    price: 999,
    description: 'A planned tier for a more active search.',
  },
]

export default function Subscriptions() {
  // Pricing is a preview, not a checkout or a claim about unimplemented entitlements.
  // see docs/CONCEPTS.md#subscription-preview
  return (
    <div className="stack page-stack">
      <section>
        <span className="eyebrow">PLAN YOUR NEXT CHAPTER</span>
        <h1>Simple plans. Clear prices.</h1>
        <p className="lead">
          A preview of what’s planned for Ajiri. Subscriptions are not available
          to purchase yet.
        </p>
      </section>
      <div className="plans-grid">
        {plans.map((plan) => (
          <Card key={plan.name} className="plan-card">
            <Badge>Preview only</Badge>
            <h2 className="mt-6">{plan.name}</h2>
            <p className="plan-price">
              KES {plan.price.toLocaleString('en-KE')}
            </p>
            <p className="muted">{plan.description}</p>
            <p className="status-text">
              Billing periods, included features and usage limits will be
              confirmed before launch.
            </p>
            <p className="font-semibold mt-6">Not yet purchasable</p>
          </Card>
        ))}
      </div>
      <Card>
        <h2>No payment needed for this preview</h2>
        <p className="muted">
          You cannot select, buy or upgrade a plan here. No payment details are
          collected, and this page does not change your account access.
        </p>
        <Button asChild variant="outline">
          <Link to="/">Explore jobs</Link>
        </Button>
      </Card>
    </div>
  )
}
