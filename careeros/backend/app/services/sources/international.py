"""International remote job source adapters.

These adapters use official public APIs for international remote job platforms.
No authentication required for basic access.

Sources implemented:
- Remote OK (https://remoteok.com/api)
- Himalayas (https://himalayas.app/api)

Each adapter is independently testable and replaceable.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.services.job_normalizer import RawJob
from app.services.job_sources import BaseJobSource, JobSourceError
from app.services.sources.html_parser import clean_text, parse_date_flexible

logger = logging.getLogger("app.jobs")


class RemoteOKSource(BaseJobSource):
    """Remote OK — https://remoteok.com/api

    Uses the official public API at https://remoteok.com/api
    Returns JSON array of job postings.
    """

    source_id = "remote_ok"
    name = "Remote OK"
    category = "remote"
    source_type = "remote"
    integration_method = "api"
    base_url = "https://remoteok.com/"
    country = "WW"

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        """Fetch jobs from Remote OK API."""
        url = "https://remoteok.com/api"
        try:
            resp = self._get(url, params={"limit": max_results})
        except JobSourceError:
            raise

        try:
            data = resp.json()
        except Exception as exc:
            raise JobSourceError(f"Remote OK: failed to parse JSON: {exc}") from exc

        # First element is metadata, rest are jobs
        if not data or not isinstance(data, list) or len(data) < 2:
            logger.info("Source %s: no jobs found", self.source_id)
            return []

        jobs_data = data[1:]  # Skip metadata
        jobs: list[RawJob] = []

        for item in jobs_data[:max_results]:
            try:
                job = self._parse_job(item)
                if job:
                    jobs.append(job)
            except Exception as exc:
                logger.warning("Source %s: failed to parse job item: %s", self.source_id, exc)
                continue

        logger.info("Source %s: fetched %d jobs", self.source_id, len(jobs))
        return jobs

    def _parse_job(self, item: dict) -> Optional[RawJob]:
        """Parse a Remote OK job item into RawJob."""
        title = item.get("position") or item.get("title")
        if not title:
            return None

        company = item.get("company") or ""
        description = item.get("description") or ""
        location = item.get("location") or ""
        url = item.get("url") or item.get("apply_url") or ""
        source_job_id = str(item.get("id") or url)

        # Parse date
        date_posted = item.get("date") or item.get("epoch")
        posted_at = parse_date_flexible(date_posted) if date_posted else None

        # Tags/skills
        tags = item.get("tags") or []
        skills = ", ".join(tags) if tags else None

        # Determine workplace type
        is_remote = True
        workplace_type = "remote"

        # Salary
        salary_min = None
        salary_max = None
        salary_currency = None
        if item.get("salary"):
            salary_text = str(item.get("salary"))
            if "-" in salary_text:
                parts = salary_text.split("-")
                try:
                    salary_min = float(parts[0].strip().replace(",", "").replace("$", ""))
                    salary_max = float(parts[1].strip().replace(",", "").replace("$", ""))
                    salary_currency = "USD"
                except (ValueError, IndexError):
                    pass

        # Determine eligibility
        eligibility, reason = self._determine_eligibility({
            "country": "WW",
            "workplace_type": "remote",
            "description": description,
            "location": location,
        })

        return RawJob(
            source=self.source_id,
            source_job_id=source_job_id,
            source_url=url,
            title=clean_text(title),
            company_name=clean_text(company),
            description=clean_text(description) if description else None,
            location=clean_text(location) if location else None,
            employment_type=None,
            skills=skills,
            posted_at=posted_at,
            is_remote=is_remote,
            workplace_type=workplace_type,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            eligibility=eligibility,
            eligibility_reason=reason,
        )

    def _determine_eligibility(self, job_data: dict) -> tuple[str, str]:
        """Determine Pakistan eligibility for Remote OK jobs.

        Most Remote OK jobs are "Remote Worldwide" which means Pakistan eligible.
        Some may have timezone restrictions or specific country restrictions.
        """
        description = job_data.get("description", "") or ""
        location = job_data.get("location", "") or ""
        desc_lower = description.lower()
        loc_lower = location.lower()

        # Check for timezone restrictions
        timezone_restrictions = ["us timezone", "america timezone", "est timezone", "pst timezone", "cst timezone"]
        if any(tz in desc_lower for tz in timezone_restrictions):
            return "ineligible", "Timezone restriction: US timezone required"

        # Check for country restrictions
        restricted_locations = ["united states only", "usa only", "canada only", "uk only", "eu only", "europe only"]
        if any(loc in loc_lower for loc in restricted_locations):
            return "ineligible", f"Location restriction: {location}"

        # Check for explicit Pakistan/Worldwide
        if "worldwide" in loc_lower or "anywhere" in loc_lower or "global" in loc_lower:
            return "eligible", "Remote worldwide"

        # Check description for Pakistan eligibility
        if "pakistan" in desc_lower and ("accept" in desc_lower or "open" in desc_lower or "welcome" in desc_lower):
            return "eligible", "Explicit Pakistan applicants accepted"

        # Default: Remote OK jobs are typically worldwide remote
        return "eligible", "Remote worldwide (Remote OK default)"


class HimalayasSource(BaseJobSource):
    """Himalayas — https://himalayas.app/api

    Uses the official public API at https://himalayas.app/jobs/api
    Returns JSON with jobs array and cursor pagination.
    """

    source_id = "himalayas"
    name = "Himalayas"
    category = "remote"
    source_type = "remote"
    integration_method = "api"
    base_url = "https://himalayas.app/"
    country = "WW"

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        """Fetch jobs from Himalayas API with cursor pagination.

        Himalayas API supports cursor-based pagination with max 20 jobs per page.
        """
        url = "https://himalayas.app/jobs/api"
        jobs: list[RawJob] = []
        cursor = None
        fetched = 0

        while fetched < max_results:
            params = {"limit": min(20, max_results - fetched)}
            if cursor:
                params["cursor"] = cursor

            try:
                resp = self._get(url, params=params)
            except JobSourceError:
                raise

            try:
                data = resp.json()
            except Exception as exc:
                raise JobSourceError(f"Himalayas: failed to parse JSON: {exc}") from exc

            if not isinstance(data, dict):
                logger.warning("Himalayas: unexpected response format")
                break

            jobs_data = data.get("jobs", [])
            if not isinstance(jobs_data, list) or not jobs_data:
                logger.info("Source %s: no more jobs found", self.source_id)
                break

            for item in jobs_data:
                if fetched >= max_results:
                    break
                try:
                    job = self._parse_job(item)
                    if job:
                        jobs.append(job)
                        fetched += 1
                except Exception as exc:
                    logger.warning("Source %s: failed to parse job item: %s", self.source_id, exc)
                    continue

            # Get next cursor for pagination
            cursor = data.get("nextCursor")
            if not cursor:
                logger.info("Source %s: no more pages (cursor exhausted)", self.source_id)
                break

        logger.info("Source %s: fetched %d jobs", self.source_id, len(jobs))
        return jobs

    def _parse_job(self, item: dict) -> Optional[RawJob]:
        """Parse a Himalayas job item into RawJob.

        Handles the official Himalayas API response schema:
        - id, title, description, location, url, applyUrl
        - company: {name, logo, website, etc.}
        - employmentType, isRemote, publishedAt, createdAt
        - salaryMin, salaryMax, salaryCurrency
        - skills: []
        - locationRestrictions, timezoneRestrictions
        - expiryDate, guid
        """
        title = item.get("title")
        if not title:
            return None

        company_data = item.get("company", {})
        company = company_data.get("name", "") if isinstance(company_data, dict) else str(company_data)

        description = item.get("description") or ""
        location = item.get("location") or ""
        # Prefer applyUrl over url for the original application link
        url = item.get("applyUrl") or item.get("url") or ""
        source_job_id = str(item.get("guid") or item.get("id") or url)

        # Parse date - prefer publishedAt, fallback to createdAt
        date_posted = item.get("publishedAt") or item.get("createdAt")
        posted_at = parse_date_flexible(date_posted) if date_posted else None

        # Skills
        skills_list = item.get("skills") or []
        skills = ", ".join(skills_list) if skills_list else None

        # Employment type
        employment_type = item.get("employmentType")
        if employment_type:
            employment_type = employment_type.lower().replace("-", "_")

        # Determine workplace type
        is_remote = item.get("isRemote", True)
        workplace_type = "remote" if is_remote else "onsite"

        # Salary
        salary_min = None
        salary_max = None
        salary_currency = None
        if item.get("salaryMin") is not None:
            salary_min = float(item["salaryMin"])
        if item.get("salaryMax") is not None:
            salary_max = float(item["salaryMax"])
        if item.get("salaryCurrency"):
            salary_currency = item["salaryCurrency"]

        # Determine eligibility - pass location restrictions and timezone restrictions
        eligibility, reason = self._determine_eligibility({
            "country": "WW",
            "workplace_type": workplace_type,
            "description": description,
            "location": location,
            "location_restrictions": item.get("locationRestrictions"),
            "timezone_restrictions": item.get("timezoneRestrictions"),
        })

        return RawJob(
            source=self.source_id,
            source_job_id=source_job_id,
            source_url=url,
            title=clean_text(title),
            company_name=clean_text(company),
            description=clean_text(description) if description else None,
            location=clean_text(location) if location else None,
            employment_type=employment_type,
            skills=skills,
            posted_at=posted_at,
            is_remote=is_remote,
            workplace_type=workplace_type,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            eligibility=eligibility,
            eligibility_reason=reason,
        )

    def _determine_eligibility(self, job_data: dict) -> tuple[str, str]:
        """Determine Pakistan eligibility for Himalayas jobs.

        Himalayas jobs are typically remote worldwide.
        Some may have timezone or location restrictions.
        Uses locationRestrictions and timezoneRestrictions from API when available.
        """
        description = job_data.get("description", "") or ""
        location = job_data.get("location", "") or ""
        location_restrictions = job_data.get("location_restrictions") or []
        timezone_restrictions = job_data.get("timezone_restrictions") or []
        desc_lower = description.lower()
        loc_lower = location.lower()

        # Check API-provided timezone restrictions first
        if timezone_restrictions:
            for tz in timezone_restrictions:
                tz_lower = str(tz).lower()
                if any(r in tz_lower for r in ["us", "america", "est", "pst", "cst", "mst"]):
                    return "ineligible", f"Timezone restriction: {tz}"

        # Check API-provided location restrictions
        if location_restrictions:
            for loc in location_restrictions:
                loc_lower = str(loc).lower()
                if any(r in loc_lower for r in ["united states", "usa", "canada", "united kingdom", "uk", "europe", "eu"]):
                    return "ineligible", f"Location restriction: {loc}"

        # Check for timezone restrictions in description
        timezone_keywords = ["us timezone", "america timezone", "est timezone", "pst timezone", "cst timezone", "only us", "only usa", "united states only"]
        if any(tz in desc_lower for tz in timezone_keywords):
            return "ineligible", "Timezone restriction: US timezone required"

        # Check for country restrictions in description/location
        restricted_locations = ["united states only", "usa only", "canada only", "uk only", "eu only", "europe only"]
        if any(loc in loc_lower for loc in restricted_locations):
            return "ineligible", f"Location restriction: {location}"

        # Check for explicit worldwide/anywhere
        if "worldwide" in loc_lower or "anywhere" in loc_lower or "global" in loc_lower:
            return "eligible", "Remote worldwide"

        # Check description for Pakistan eligibility
        if "pakistan" in desc_lower and ("accept" in desc_lower or "open" in desc_lower or "welcome" in desc_lower):
            return "eligible", "Explicit Pakistan applicants accepted"

        # Default: Himalayas jobs are typically worldwide remote
        return "eligible", "Remote worldwide (Himalayas default)"