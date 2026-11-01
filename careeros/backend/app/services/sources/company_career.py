"""Company career page source adapter.

Supports legitimate public career pages by parsing JSON-LD / schema.org
JobPosting structured data embedded in the HTML.

This is a general-purpose adapter that works with any company career page
that follows the schema.org JobPosting convention. It does NOT do generic
HTML scraping — it looks for structured JSON-LD blocks.

For company-specific adapters that need custom HTML parsing, subclass this
or create a new adapter.
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from urllib.parse import urljoin

from app.services.job_normalizer import RawJob
from app.services.job_sources import BaseJobSource, JobSourceError
from app.services.sources.html_parser import clean_text, parse_html

logger = logging.getLogger("app.jobs")


class CompanyCareerSource(BaseJobSource):
    """General-purpose company career page adapter.

    Parses JSON-LD structured data (schema.org JobPosting) from company
    career pages. This works with any ATS that emits JSON-LD JobPosting
    blocks (Greenhouse, Lever, Workday, etc. often do).

    Configuration:
    - ``career_page_url``: The company's public careers page URL.
    - ``company_name``: Override the company name (defaults to class name).
    - ``max_pages``: Maximum pagination pages to crawl.
    """

    category = "company_career"
    source_type = "company_career"
    integration_method = "json_ld"
    country = "PK"

    # These must be set per-company
    career_page_url: str = ""
    company_name: str = ""

    # CSS selector for the container of individual job listings on the career page
    job_list_selector: str = ".job, .career-job, [data-job-id]"
    # Max pagination pages
    max_pages: int = 5

    def _extract_job_postings_from_jsonld(self, soup) -> list[dict]:
        """Extract JobPosting JSON-LD blocks from a BeautifulSoup tree."""
        postings = []
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and self._is_job_posting(item):
                        postings.append(item)
            elif isinstance(data, dict):
                if self._is_job_posting(data):
                    postings.append(data)
                elif "@graph" in data:
                    for item in data["@graph"]:
                        if isinstance(item, dict) and self._is_job_posting(item):
                            postings.append(item)

        return postings

    def _is_job_posting(self, data: dict) -> bool:
        """Check if a JSON-LD dict represents a JobPosting."""
        type_val = data.get("@type", "")
        if isinstance(type_val, list):
            return "JobPosting" in type_val
        return type_val == "JobPosting"

    def _jsonld_to_rawjob(self, posting: dict, career_page_url: str) -> Optional[RawJob]:
        """Convert a schema.org JobPosting dict to a RawJob."""
        title = posting.get("title") or posting.get("jobTitle")
        if not title:
            return None

        company = (
            posting.get("hiringOrganization", {})
            if isinstance(posting.get("hiringOrganization"), dict)
            else {"name": posting.get("hiringOrganization")}
        )
        company_name = company.get("name") if isinstance(company, dict) else str(company) or self.company_name

        location_obj = posting.get("jobLocation", {})
        if isinstance(location_obj, dict):
            address = location_obj.get("address", {})
            if isinstance(address, dict):
                city = address.get("addressLocality", "")
                region = address.get("addressRegion", "")
                country = address.get("addressCountry", "")
                location = ", ".join(filter(None, [city, region, country]))
            else:
                location = str(address) if address else None
        else:
            location = str(location_obj) if location_obj else None

        date_posted = posting.get("datePosted")
        valid_through = posting.get("validThrough")

        employment_type = posting.get("employmentType")
        # Map schema.org employment types to our vocabulary
        et_map = {
            "FULL_TIME": "full_time",
            "FULL_TIME_PERMANENT": "full_time",
            "PART_TIME": "part_time",
            "CONTRACT": "contract",
            "TEMPORARY": "temporary",
            "INTERNSHIP": "internship",
        }
        employment = et_map.get(employment_type.upper() if employment_type else "") if employment_type else None

        description = posting.get("description", "")
        if isinstance(description, str):
            description = description.strip()

        source_url = posting.get("applyLink", {}).get("href") if isinstance(posting.get("applyLink"), dict) else posting.get("url")
        if not source_url:
            source_url = career_page_url

        source_job_id = posting.get("id") or posting.get("identifier", {}).get("value", "") if isinstance(posting.get("identifier"), dict) else ""
        if not source_job_id:
            source_job_id = source_url

        from app.services.sources.html_parser import parse_date_flexible
        posted_at = parse_date_flexible(date_posted) if date_posted else None
        closing_at = parse_date_flexible(valid_through) if valid_through else None

        incentives = posting.get("incentiveSalary", {})
        if isinstance(incentives, dict):
            salary_currency = incentives.get("currency", "PKR") if "currency" in incentives else None
            salary_min = None
            salary_max = None
            value = incentives.get("value", "")
            if value:
                value_str = str(value)
                try:
                    if "-" in value_str:
                        parts = value_str.split("-")
                        salary_min = float(parts[0].strip().replace(",", ""))
                        salary_max = float(parts[1].strip().replace(",", ""))
                    else:
                        salary_min = salary_max = float(value_str.replace(",", ""))
                except (ValueError, IndexError):
                    pass
        elif isinstance(incentives, str):
            salary_currency = None
            salary_min = salary_max = None
        else:
            salary_currency = None
            salary_min = salary_max = None

        responsibilities = posting.get("responsibilities", {})
        if isinstance(responsibilities, dict):
            responsibilities = responsibilities.get("@type")
            # Actually responsibilities should be a string
            responsibilities = posting.get("responsibilities")
        responsibilities_text = responsibilities if isinstance(responsibilities, str) else None

        return RawJob(
            source=self.source_id,
            source_job_id=str(source_job_id),
            source_url=source_url,
            title=clean_text(title),
            company_name=clean_text(company_name) or company_name,
            description=clean_text(description) if description else None,
            requirements=responsibilities_text,
            employment_type=employment,
            location=clean_text(location) if location else None,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            posted_at=posted_at,
            closing_at=closing_at,
            is_remote=False,
            eligibility=self._determine_eligibility({
                "country": location or "" if location else "",
                "workplace_type": "onsite",
                "description": description or "",
            })[0],
            eligibility_reason=self._determine_eligibility({
                "country": location or "" if location else "",
                "workplace_type": "onsite",
                "description": description or "",
            })[1],
        )

    def fetch(self, *, max_results: int = 200, timeout: float = 20.0) -> list[RawJob]:
        if not self.career_page_url:
            raise JobSourceError(f"Source {self.source_id} has no career_page_url configured")

        jobs: list[RawJob] = []
        for page in range(1, self.max_pages + 1):
            url = self.career_page_url if page == 1 else urljoin(self.career_page_url, f"?page={page}")
            try:
                resp = self._get(url)
            except JobSourceError:
                if page == 1:
                    raise
                break

            soup = parse_html(resp.text)
            postings = self._extract_job_postings_from_jsonld(soup)

            if not postings:
                # Also try direct HTML parsing for job listings
                postings = self._parse_html_fallback(soup, url)

            if not postings:
                break

            for posting in postings:
                if len(jobs) >= max_results:
                    break
                raw = self._jsonld_to_rawjob(posting, url)
                if raw:
                    jobs.append(raw)

        return jobs

    def _parse_html_fallback(self, soup, url: str) -> list[dict]:
        """Fallback HTML parsing for career pages without JSON-LD."""
        jobs = []
        items = soup.select(self.job_list_selector)
        for item in items:
            title_elem = item.select_one(".job-title, h3, h4, a")
            title = clean_text(title_elem.get_text()) if title_elem else None
            if title:
                jobs.append({"title": title, "description": clean_text(item.get_text())})
        return jobs

    def _determine_eligibility(self, job_data: dict) -> tuple[str, str]:
        """Determine Pakistan eligibility based on job location and restrictions.

        Returns (eligibility_status, reason) where status is one of:
        - "eligible": Pakistan applicants are accepted or no restrictions
        - "ineligible": Work authorization/visa restrictions prevent Pakistani applicants
        - "unknown": Insufficient information to determine
        """
        # Check country field
        country = job_data.get("country", "") or ""
        if country:
            country_upper = country.upper()
            if country_upper == "PK":
                return "eligible", "Country is Pakistan"
            restricted_countries = {"US", "CA", "GB", "AU"}
            if country_upper in restricted_countries:
                return "ineligible", f"Country restriction: {country} applicants not accepted"
            return "unknown", f"Country restriction: {country}"
        
        # Check workplace type
        workplace_type = job_data.get("workplace_type", "") or ""
        if workplace_type == "remote":
            location = job_data.get("location", "") or ""
            location_upper = location.upper()
            if any(loc in location_upper for loc in ["USA", "CA", "GB", "AU"]):
                return "ineligible", f"Remote position restricted to {location}"
            return "eligible", "Remote worldwide"
        
        # Check description for Pakistan eligibility
        description = job_data.get("description", "") or ""
        desc_lower = description.lower()
        if "pakistan applicants" in desc_lower or "open to pk" in desc_lower:
            return "eligible", "Explicit Pakistan applicants accepted"
        
        return "unknown", "Eligibility cannot be determined from available data"
