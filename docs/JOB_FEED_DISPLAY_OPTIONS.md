# Supplemental feed browsing

The selected policy is authenticated browsing of supplemental feed results posted
within **14 days**, with availability explicitly unverified. Missing/future dates,
inactive rows, scams and known closed listings are excluded. Application, alert,
saved-search and public publication eligibility is never widened.

The singleton admin value replaces `JOB_FEED_DISPLAY_ENABLED`; that retired flag
cannot enable anything. The additive migration seeds **off**. Only Michael may
activate it. Follow the [maintenance operator procedure](../maintenance/README.md#supplemental-job-browsing)
for menu, cache delay, audit, counts, smoke tests, force-off and private admin-path
configuration. Historical A/B/C choices and environment activation instructions
are superseded by the selected 14-day policy.
