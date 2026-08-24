def calculate_match_score(profile, job):
    """
    Returns a 0-100 integer representing how well a profile's skills
    overlap with a job's required skills.

    Deliberately simple for v1: percentage of the job's required skills
    that the profile actually has. A job with no listed skills always
    scores 0 — there's nothing concrete to match against, so we don't
    want to claim a false 100% match.
    """
    job_skill_ids = set(job.skills_required.values_list('id', flat=True))

    if not job_skill_ids:
        return 0

    profile_skill_ids = set(profile.skills.values_list('id', flat=True))

    matched = job_skill_ids & profile_skill_ids
    score = round((len(matched) / len(job_skill_ids)) * 100)

    return score