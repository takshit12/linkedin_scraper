"""
Data loader for scraped job data (JSON/CSV)
"""
import json
import csv
from typing import List, Dict, Optional
from .utils import validate_profile_url, normalize_profile_url, extract_profile_id


def load_jobs_from_json(filepath: str) -> List[Dict]:
    """
    Load scraped job data from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        List of job dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        jobs = json.load(f)

    if not isinstance(jobs, list):
        raise ValueError("JSON file must contain a list of jobs")

    return jobs


def load_jobs_from_csv(filepath: str) -> List[Dict]:
    """
    Load scraped job data from CSV file.

    Args:
        filepath: Path to CSV file

    Returns:
        List of job dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    jobs = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(dict(row))

    return jobs


def filter_jobs_with_posters(jobs: List[Dict]) -> List[Dict]:
    """
    Filter jobs that have valid poster profile URLs.

    Args:
        jobs: List of job dictionaries

    Returns:
        List of jobs that have poster_profile_url field populated
    """
    filtered = []

    for job in jobs:
        poster_url = job.get('poster_profile_url')

        if poster_url and validate_profile_url(poster_url):
            filtered.append(job)

    return filtered


def deduplicate_profiles(jobs: List[Dict]) -> List[Dict]:
    """
    Remove duplicate poster profiles.
    If the same person posted multiple jobs, keep only the first one.

    Args:
        jobs: List of job dictionaries

    Returns:
        List of jobs with unique poster profiles
    """
    seen_profile_ids = set()
    unique_jobs = []

    for job in jobs:
        poster_url = job.get('poster_profile_url')
        if not poster_url:
            continue

        # Normalize and extract ID
        normalized_url = normalize_profile_url(poster_url)
        profile_id = extract_profile_id(normalized_url)

        if profile_id and profile_id not in seen_profile_ids:
            seen_profile_ids.add(profile_id)
            # Update job with normalized URL
            job['poster_profile_url'] = normalized_url
            job['poster_profile_id'] = profile_id
            unique_jobs.append(job)

    return unique_jobs


def load_and_prepare_data(filepath: str) -> List[Dict]:
    """
    Load job data, filter for posters, and deduplicate.

    This is the main function to use for loading data.

    Args:
        filepath: Path to JSON or CSV file

    Returns:
        List of unique job posters ready for connection requests

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    # Determine file type
    if filepath.endswith('.json'):
        jobs = load_jobs_from_json(filepath)
    elif filepath.endswith('.csv'):
        jobs = load_jobs_from_csv(filepath)
    else:
        raise ValueError("File must be .json or .csv format")

    print(f"✓ Loaded {len(jobs)} jobs from {filepath}")

    # Filter for jobs with poster info
    jobs_with_posters = filter_jobs_with_posters(jobs)
    print(f"✓ Found {len(jobs_with_posters)} jobs with poster profiles")

    # Deduplicate by profile
    unique_profiles = deduplicate_profiles(jobs_with_posters)
    print(f"✓ Identified {len(unique_profiles)} unique poster profiles")

    return unique_profiles


def get_profile_summary(job: Dict) -> str:
    """
    Get a human-readable summary of a job poster.

    Args:
        job: Job dictionary

    Returns:
        Summary string like "John Doe (AI Engineer at OpenAI)"
    """
    name = job.get('poster_name', 'Unknown')
    title = job.get('job_title', 'Unknown Position')
    company = job.get('company', 'Unknown Company')

    return f"{name} ({title} at {company})"


def export_profiles_summary(jobs: List[Dict], output_file: str):
    """
    Export a summary of profiles to CSV.

    Args:
        jobs: List of job dictionaries
        output_file: Path to output CSV file
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'poster_profile_id',
            'poster_profile_url',
            'poster_name',
            'poster_headline',
            'job_title',
            'company',
            'location'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for job in jobs:
            row = {
                'poster_profile_id': job.get('poster_profile_id', ''),
                'poster_profile_url': job.get('poster_profile_url', ''),
                'poster_name': job.get('poster_name', ''),
                'poster_headline': job.get('poster_headline', ''),
                'job_title': job.get('job_title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', '')
            }
            writer.writerow(row)

    print(f"✓ Exported profile summary to {output_file}")
