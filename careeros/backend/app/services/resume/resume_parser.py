"""Resume text parser for importing resumes from plain text.

Parses plain text resumes into structured sections using common header detection.
This is a deterministic parser — no LLM calls.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class ResumeTextParser:
    """Parse plain text resumes into structured sections.
    
    Uses section header detection to split text into standard resume sections:
    - Summary/Objective/Profile
    - Skills
    - Experience/Work History
    - Education
    - Projects
    - Certifications
    
    Sections are identified by common headers (e.g., "Experience", "Education").
    Content between headers belongs to that section.
    """

    SECTION_HEADERS = {
        "summary": [
            "summary", "objective", "profile", "about me", "about",
            "professional summary", "career summary", "personal profile",
        ],
        "skills": [
            "skills", "technical skills", "core competencies",
            "proficiencies", "technologies", "tech stack",
        ],
        "experience": [
            "experience", "work experience", "employment history",
            "professional experience", "career history", "work history",
        ],
        "education": [
            "education", "academic background", "educational background",
            "qualifications", "degrees", "study",
        ],
        "projects": [
            "projects", "project experience", "key projects",
            "personal projects", "portfolio",
        ],
        "certifications": [
            "certifications", "certificates", "credentials",
            "professional certifications", "licenses",
        ],
        "achievements": [
            "achievements", "accomplishments", "awards", "honors",
            "recognitions",
        ],
        "volunteer": [
            "volunteer", "volunteer experience", "community",
        ],
        "publications": [
            "publications", "published work", "research",
        ],
    }

    def __init__(self) -> None:
        # Pre-compile section header regex patterns
        self._header_patterns: Dict[str, List[re.Pattern]] = {}
        for section_type, headers in self.SECTION_HEADERS.items():
            self._header_patterns[section_type] = [
                re.compile(rf'^[{re.escape(h)}]{{0,1}}\s*{re.escape(h)}\s*[:]*\s*$', re.IGNORECASE)
                for h in headers
            ]
            # Also add pattern for headers with dashes
            self._header_patterns[section_type].extend([
                re.compile(rf'^{re.escape(h)}\s*[-–—:]+$', re.IGNORECASE)
                for h in headers
            ])

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse plain text resume into structured sections.
        
        Returns a dict with standard resume section keys.
        Unknown content between recognized headers is stored under "other".
        """
        if not text or not text.strip():
            return {}

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = text.split('\n')

        # Detect sections
        sections: Dict[str, List[str]] = {}
        current_section: Optional[str] = None
        current_lines: List[str] = []
        section_line_indices: List[Tuple[int, str]] = []  # (line_index, section_type)

        for i, line in enumerate(lines):
            detected_section = self._detect_section_header(line)
            if detected_section:
                # Save previous section
                if current_section and current_lines:
                    sections.setdefault(current_section, []).extend(
                        l for l in current_lines if l.strip()
                    )
                # Start new section
                current_section = detected_section
                current_lines = []
                section_line_indices.append((i, detected_section))
            else:
                if current_section is not None:
                    current_lines.append(line)

        # Save last section
        if current_section and current_lines:
            sections.setdefault(current_section, []).extend(
                l for l in current_lines if l.strip()
            )

        # If no sections detected, put everything in summary
        if not sections and text.strip():
            sections["summary"] = [text.strip()]

        # Convert section line lists to structured content
        structured: Dict[str, Any] = {}

        for section_type, lines_list in sections.items():
            content = "\n".join(lines_list).strip()
            if not content:
                continue

            # Parse section-specific content
            if section_type == "skills":
                structured["skills"] = self._parse_skills(content)
            elif section_type == "experience":
                structured["experience"] = self._parse_experience(content)
            elif section_type == "education":
                structured["education"] = self._parse_education(content)
            elif section_type == "projects":
                structured["projects"] = self._parse_projects(content)
            elif section_type == "certifications":
                structured["certifications"] = self._parse_certifications(content)
            elif section_type == "summary":
                structured["summary"] = content
            elif section_type == "achievements":
                structured["achievements"] = content.split('\n')
            else:
                # Custom or other section
                structured.setdefault("custom_sections", {})[section_type] = content

        # Ensure standard empty sections exist
        for key in ["skills", "experience", "education", "projects", "certifications", "achievements"]:
            if key not in structured:
                structured[key] = [] if key != "summary" else (structured.get("summary", "") or "")

        return structured

    def _detect_section_header(self, line: str) -> Optional[str]:
        """Check if a line is a section header and return the section type."""
        line_stripped = line.strip()
        if not line_stripped:
            return None

        # Check for all-uppercase headers (common in resumes)
        if line_stripped.isupper() and len(line_stripped) > 2:
            upper = line_stripped.lower()
            for section_type, headers in self.SECTION_HEADERS.items():
                for header in headers:
                    if header in upper:
                        return section_type

        # Check against compiled patterns
        for section_type, patterns in self._header_patterns.items():
            for pattern in patterns:
                if pattern.match(line_stripped):
                    return section_type

        # Check if line matches a header keyword exactly
        for section_type, headers in self.SECTION_HEADERS.items():
            for header in headers:
                if line_stripped.lower().rstrip(':- ') == header:
                    return section_type

        return None

    def _parse_skills(self, content: str) -> List[Dict[str, Any]]:
        """Parse skills from section content."""
        skills = []
        
        # Try to split by common separators
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet points
            line = re.sub(r'^[\u2022\-\*•]\s*', '', line)
            
            # Split by commas if single line with multiple skills
            if ',' in line and not line.endswith(':'):
                parts = [p.strip() for p in line.split(',') if p.strip()]
            else:
                # Could be a single skill with category
                parts = [line]
            
            for part in parts:
                # Skip category headers like "Technical Skills:"
                if part.endswith(':') or part.lower() in ("technical skills", "soft skills", "languages"):
                    continue
                
                skill_name = part.strip().rstrip(':').strip()
                if skill_name and len(skill_name) > 1:
                    skills.append({
                        "name": skill_name,
                        "category": "technical",  # Default category
                        "proficiency": None,
                        "years_of_experience": None,
                    })
        
        return skills

    def _parse_experience(self, content: str) -> List[Dict[str, Any]]:
        """Parse work experience from section content."""
        experiences = []
        
        # Split into job blocks (typically separated by blank lines or dates)
        job_blocks = self._split_into_blocks(content)
        
        for block in job_blocks:
            exp = self._parse_job_block(block)
            if exp:
                experiences.append(exp)
        
        return experiences

    def _parse_job_block(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single job experience block."""
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            return None
        
        # First line(s) typically have: title, company, date range
        # Look for date patterns
        date_pattern = re.compile(
            r'(\d{1,2}/\d{4}|\d{4}|\w+ \d{4}|[A-Z][a-z]+ \d{4})\s*(?:-|to|–|—)\s*(\d{1,2}/\d{4}|\d{4}|present|current|\w+ \d{4}|[A-Z][a-z]+ \d{4})?',
            re.IGNORECASE
        )
        
        # Find the first line with date info
        first_line_idx = 0
        date_match = None
        for i, line in enumerate(lines):
            match = date_pattern.search(line)
            if match:
                first_line_idx = i
                date_match = match
                break
        
        if date_match:
            start_date_str = date_match.group(1)
            end_date_str = date_match.group(2) if date_match.group(2) else None
            is_current = end_date_str is None or end_date_str.lower() in ("present", "current")
        else:
            start_date_str = None
            end_date_str = None
            is_current = False
        
        # First line (or first non-date part) has title/company
        company = None
        job_title = None
        if first_line_idx == 0 and lines:
            # Check if date is on first line
            if date_match:
                parts = re.split(date_pattern, lines[0])
                # Try to extract title and company
                header = parts[0].strip()
                # Split by common separators
                if '|' in header:
                    parts2 = header.split('|')
                    job_title = parts2[0].strip()
                    company = parts2[1].strip() if len(parts2) > 1 else None
                elif re.search(r'\bat\b', header, re.IGNORECASE):
                    parts2 = re.split(r'\bat\b', header, flags=re.IGNORECASE)
                    job_title = parts2[0].strip()
                    company = parts2[1].strip() if len(parts2) > 1 else None
                else:
                    job_title = header
                    company = None
            else:
                job_title = lines[0]
                company = None
        elif lines:
            job_title = lines[first_line_idx] if first_line_idx < len(lines) else None
            company = None
        
        # Collect description from remaining lines
        description = "\n".join(lines[1:]) if len(lines) > 1 else ""
        
        # Clean up description - extract bullet points
        bullets = []
        for line in lines[1:]:
            if re.match(r'^[\u2022\-\*•]\s', line):
                bullets.append(line.lstrip('\u2022\\-*').strip())
        
        if not bullets and description:
            bullets = [description]
        
        return {
            "company": company or "Unknown Company",
            "job_title": job_title or "Unknown Position",
            "location": None,
            "start_date": self._parse_date(start_date_str) if start_date_str else None,
            "end_date": None,
            "is_current": is_current,
            "description": "\n".join(f"- {b}" for b in bullets) if bullets else None,
        }

    def _split_into_blocks(self, content: str) -> List[str]:
        """Split content into blocks separated by blank lines."""
        blocks = []
        current_block = []
        
        for line in content.split('\n'):
            if line.strip():
                current_block.append(line)
            else:
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
        
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks

    def _parse_education(self, content: str) -> List[Dict[str, Any]]:
        """Parse education entries from section content."""
        educations = []
        
        blocks = self._split_into_blocks(content)
        
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines:
                continue
            
            # Look for degree and institution
            degree = None
            institution = None
            field_of_study = None
            
            first_line = lines[0]
            
            # Common patterns: "Bachelor of Science in Computer Science, University Name"
            # or "University Name - Bachelor of Arts"
            degree_match = re.search(
                r'(bachelor[\'"]?s?|master[\'"]?s?|ph\.?d\.?|b\.?sc\.?|m\.?sc\.?|mba|associate[\'"]?s?)',
                first_line, re.IGNORECASE
            )
            
            if degree_match:
                degree = degree_match.group(1).strip()
            
            # Look for institution (often after degree or on separate line)
            if ',' in first_line:
                # "BS Computer Science, University of X"
                parts = first_line.split(',')
                if degree:
                    institution = parts[-1].strip()
                else:
                    institution = first_line
            else:
                institution = first_line
            
            # Look for field of study
            if ' in ' in first_line.lower():
                field_match = re.search(r'in\s+(.+?)(?:,|$)', first_line, re.IGNORECASE)
                if field_match:
                    field_of_study = field_match.group(1).strip()
            
            educations.append({
                "institution": institution,
                "degree": degree,
                "field_of_study": field_of_study,
                "start_date": None,
                "end_date": None,
                "grade": None,
                "description": None,
            })
        
        return educations

    def _parse_projects(self, content: str) -> List[Dict[str, Any]]:
        """Parse project entries from section content."""
        projects = []
        
        blocks = self._split_into_blocks(content)
        
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines:
                continue
            
            project_name = lines[0]
            # Remove bullet points
            project_name = re.sub(r'^[\u2022\-\*•]\s*', '', project_name)
            
            description = None
            bullets = []
            
            for line in lines[1:]:
                clean_line = line.lstrip('\u2022\\-*').strip()
                if clean_line:
                    bullets.append(clean_line)
            
            if bullets:
                description = "\n".join(f"- {b}" for b in bullets)
            
            projects.append({
                "name": project_name,
                "description": description,
                "url": None,
            })
        
        return projects

    def _parse_certifications(self, content: str) -> List[Dict[str, Any]]:
        """Parse certification entries from section content."""
        certifications = []
        
        # Split by lines or commas
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet points
            line = re.sub(r'^[\u2022\-\*•]\s*', '', line)
            
            # Try to parse "Name, Issuer" or "Name - Issuer (YYYY)"
            parts = re.split(r'[,\-]|\s*\(\d{4}\)', line, maxsplit=1)
            
            if len(parts) >= 2:
                name = parts[0].strip()
                issuer = parts[1].strip()
            else:
                name = line
                issuer = None
            
            # Extract date if present
            date_match = re.search(r'(\d{4})', line)
            issue_date = None
            if date_match:
                issue_date = date_match.group(1) + "-01-01"  # Just use year with Jan 1
            
            certifications.append({
                "name": name,
                "issuing_organization": issuer,
                "issue_date": issue_date,
                "expiry_date": None,
                "credential_id": None,
                "credential_url": None,
                "description": None,
            })
        
        return certifications

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse a date string into ISO format."""
        try:
            from datetime import datetime
            
            # Try various date formats
            formats = [
                "%Y-%m", "%Y", "%m/%Y", "%Y/%m",
                "%B %Y", "%b %Y", "%b %d, %Y",
                "%d %B %Y", "%d %b %Y",
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None