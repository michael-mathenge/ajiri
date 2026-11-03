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

## 3 November 2026 source evidence survey

Performed after the default-off production deployment completed. Production was
not ingested, relabelled or edited for the survey. Counts use the independently
restored 3 November 17:05 UTC snapshot, evaluated at 17:54 UTC (20:54 Nairobi).
The original cohort is reconstructed exactly: rows scraped by
1 November 17:09:00.356422 UTC, active, non-scam and excluding pilot IDs 1, 779,
980. It contains the reported **1,808** rows. All have no stored closing timestamp;
977 are archived for absent evidence and 831 are unverified.

| Configured source | Original cohort | Share of 1,808 | Posted within 14 days now | Recent share within source | All snapshot rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| MyJobMag Kenya | 1,808 | 100% | 1,104 | 61.1% | 2,029 |

There is one source, reused by GitHub ingestion and the local Celery wrapper;
these are not separate feeds. The three other stored source labels are retained
synthetic deployment/owner pilots, one row each, not configured vacancy sources.
Total stored jobs are 2,032; 12 MyJobMag rows have heuristic scam flags. That is
0.59% of the source's stored rows, not a proven fraud rate. Current supplemental
candidates number 1,313, eligible jobs zero; browsing remains off. Historical
1,808 and today's 1,313 must not be presented as interchangeable inventories.

### Machine-readable evidence

The configured [XML feed](https://www.myjobmag.co.ke/jobsxml_by_categories.xml)
returned HTTP 200, 363,474 bytes and 100 entries, parsed without errors. All entries
contain `pubDate` (publication time) and `expiryDate` (listing-expiry field), but
63 expiry values are empty. The remaining **37** are explicit future GMT timestamps,
from 5 November through 31 December 2026. These are machine fields, not dates
extracted from listing prose. The current adapter reads only `application_deadline`
or `closing_date`, neither present, so it accepts **zero** of these expiry values.

Three bounded source-page checks found explicit timezone-aware JobPosting
`validThrough` values on the same calendar day as the corresponding feed expiry.
The feed says midnight; structured page metadata says 23:59:59. The proposed
adapter uses the exact earlier feed value and never extends it. Example evidence:
[page A](https://www.myjobmag.co.ke/a_fields.php?id=1378044),
[page B](https://www.myjobmag.co.ke/a_fields.php?id=1377983),
[page C](https://www.myjobmag.co.ke/a_fields.php?id=1377981).
This sample supports the field mapping, not a claim that every listing is open.

| Population | Current adapter | Additional potential from the narrow adapter change |
| --- | ---: | ---: |
| Original 1,808 rows | 0 evidence-backed conversions | 0 observed: none of the 37 dated entries matches this cohort |
| Newer already-stored rows | 0 from this field | 0–7, subject to unchanged content, unarchived state and all existing gates |
| Current-feed entries not yet stored | 0 from this field | 0–30 through future normal ingestion, subject to all existing gates |
| Entire 100-entry feed sample | 0 from this field | At most 37 potential candidates; 63 empty values remain unverified |

These are bounded opportunities from one feed snapshot, not predicted live
inventory or authority to backfill. The older cohort's out-of-feed source pages
were not exhaustively surveyed; its latent recoverable count is unknown. Do not
extrapolate the 37% sample rate to 1,808, infer dates from prose, assume a missing
feed entry is closed, or reopen the 977 archived rows. No live conversions occurred.

### Source quality and recommendation

Keep MyJobMag as supplemental discovery with quarantine and existing gates. Its
feed is structured and reachable, but empty deadlines cover 63% of this sample;
one aggregator is not diversified verified inventory. Its
[FAQ](https://www.myjobmag.co.ke/faq) describes automatic advert duration and
employer expiry controls; its [terms](https://www.myjobmag.co.ke/terms) disclaim
authenticity guarantees and explain that expired listings can remain accessible.
Page existence is therefore insufficient evidence. No other configured vacancy
source was found to recommend dropping; leave all configuration unchanged.

Use both paths: the narrow, source-scoped expiry parser can help future ordinary
ingestion; employer-direct listings with owner verification, independent staff
review and an explicit future deadline are the stronger durable inventory path.
Do not activate employer posting, sending, public pages or browsing for this work.
The parser change is an unmerged PR candidate, not part of deployed `86cdf39`.
