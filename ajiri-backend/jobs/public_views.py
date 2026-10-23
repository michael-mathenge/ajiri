"""Anonymous job-only pages; opt-in publication never relaxes private API guards.

see docs/CONCEPTS.md#public-job-contract
"""

import json
import math
from urllib.parse import urlsplit
from xml.etree.ElementTree import Element, SubElement, tostring
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.db.models.functions import Trim
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags, escape
from django.utils.text import slugify
from django.views.decorators.http import require_safe
from .models import Job

PAGE_SIZE = 1000
EMPLOYMENT = {
    "full_time": "FULL_TIME",
    "part_time": "PART_TIME",
    "contract": "CONTRACTOR",
    "internship": "INTERN",
}


def origin():
    if not getattr(settings, "PUBLIC_JOBS_ENABLED", False):
        raise Http404
    value = getattr(settings, "PUBLIC_JOB_ORIGIN", "")
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
            or any(ord(char) < 33 for char in value)
        ):
            raise ValueError
        return value.rstrip("/")
    except (ValueError, TypeError):
        raise Http404 from None


def listings():
    return (
        Job.objects.filter(is_active=True, is_flagged_scam=False)
        .annotate(public_title=Trim("title"), public_company=Trim("company_name"))
        .exclude(public_title="")
        .exclude(public_company="")
    )


def plain(value):
    return "".join(
        char for char in strip_tags(value) if ord(char) >= 32 or char in "\n\t"
    ).strip()


def safe_source(value):
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme in ("http", "https")
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and value == value.strip()
            and not any(ord(char) < 32 for char in value)
        ):
            return value
    except (ValueError, TypeError):
        pass
    return ""


def job_path(job):
    return reverse(
        "public-job-detail",
        kwargs={"pk": job.pk, "slug": slugify(plain(job.title))[:80] or "job"},
    )


def structured_job(job, canonical):
    # An explicit country in source text is required; do not infer addressCountry
    # from a city name, invent dates/salary/expiry or claim a guaranteed rich result.
    parts = [part.strip() for part in plain(job.location).split(",") if part.strip()]
    if (
        not job.posted_at
        or job.posted_at > timezone.now()
        or not plain(job.description[:12000])
        or len(job.description) > 12000
        or len(job.requirements) > 6000
        or not safe_source(job.source_url)
        or len(parts) < 2
        or parts[-1].casefold() not in ("kenya", "ke")
        or "remote" in plain(job.location).casefold()
    ):
        return None
    description = "<p>" + str(escape(plain(job.description))) + "</p>"
    if plain(job.requirements):
        description += "<p>" + str(escape(plain(job.requirements))) + "</p>"
    result = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "url": canonical,
        "title": plain(job.title),
        "description": description,
        "datePosted": job.posted_at.isoformat(),
        "hiringOrganization": {
            "@type": "Organization",
            "name": plain(job.company_name),
        },
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": ", ".join(parts[:-1]),
                "addressCountry": "KE",
            },
        },
    }
    if job.job_type in EMPLOYMENT:
        result["employmentType"] = EMPLOYMENT[job.job_type]
    return result


def public_response(response, content_type=None):
    if not isinstance(response, HttpResponse):
        response = HttpResponse(response, content_type=content_type)
    response["Cache-Control"] = "public, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_safe
def detail(request, pk, slug):
    base = origin()
    try:
        job = listings().get(pk=pk)
    except Job.DoesNotExist:
        raise Http404 from None
    path = job_path(job)
    if request.path != path:
        return public_response(HttpResponsePermanentRedirect(base + path))
    canonical = base + path
    data = structured_job(job, canonical)
    structured = (
        json.dumps(data, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        if data
        else ""
    )
    context = {
        "title": plain(job.title),
        "company": plain(job.company_name),
        "location": plain(job.location),
        "description": plain(job.description[:12000]),
        "requirements": plain(job.requirements[:6000]),
        "truncated": len(job.description) > 12000 or len(job.requirements) > 6000,
        "posted": job.posted_at
        if job.posted_at and job.posted_at <= timezone.now()
        else None,
        "job_type": job.get_job_type_display(),
        "source": safe_source(job.source_url),
        "canonical": canonical,
        "structured": structured,
        "application_path": f"/jobs/{job.pk}",
    }
    # Deliberately no request/context processors: every visitor gets the same job-only document.
    return public_response(
        get_template("jobs/public_detail.html").render(context),
        "text/html; charset=utf-8",
    )


def xml_response(root):
    return public_response(
        tostring(root, encoding="utf-8", xml_declaration=True), "application/xml"
    )


@require_safe
def sitemap_index(request):
    base = origin()
    root = Element("sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for page in range(1, max(1, math.ceil(listings().count() / PAGE_SIZE)) + 1):
        row = SubElement(root, "sitemap")
        SubElement(row, "loc").text = base + reverse(
            "public-job-sitemap", kwargs={"page": page}
        )
    return xml_response(root)


@require_safe
def sitemap_page(request, page):
    base = origin()
    try:
        jobs = Paginator(listings().only("pk", "title").order_by("pk"), PAGE_SIZE).page(
            page
        )
    except EmptyPage:
        raise Http404 from None
    root = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for job in jobs:
        SubElement(SubElement(root, "url"), "loc").text = base + job_path(job)
    return xml_response(root)


@require_safe
def robots(request):
    base = origin()
    body = (
        "User-agent: *\nAllow: /vacancies/\nDisallow: /api/\nDisallow: /admin/\n"
        "Disallow: /media/\nDisallow: /profile\nDisallow: /applications\nDisallow: /cv-builder\n"
        "Disallow: /jobs/\nSitemap: "
        + base
        + reverse("public-job-sitemap-index")
        + "\n"
    )
    return public_response(body, "text/plain; charset=utf-8")
