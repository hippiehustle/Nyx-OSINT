"""Batch processing for multiple searches."""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from nyx.core.logger import get_logger
from nyx.osint.search import SearchService

logger = get_logger(__name__)


@dataclass
class BatchJob:
    """Batch processing job."""

    id: str
    queries: List[str]
    total: int
    completed: int
    failed: int
    results: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime]
    status: str


class BatchProcessor:
    """Process multiple searches in batch."""

    def __init__(self, max_concurrent: int = 10) -> None:
        """Initialize batch processor.

        Args:
            max_concurrent: Maximum concurrent searches
        """
        self.max_concurrent = max_concurrent
        self.search_service = SearchService()
        self.jobs: Dict[str, BatchJob] = {}

    async def process_usernames(
        self,
        usernames: List[str],
        exclude_nsfw: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Process multiple usernames in batch.

        Args:
            usernames: List of usernames to search
            exclude_nsfw: Whether to exclude NSFW platforms
            progress_callback: Callback for progress updates

        Returns:
            Batch results
        """
        import uuid

        job_id = str(uuid.uuid4())
        job = BatchJob(
            id=job_id,
            queries=usernames,
            total=len(usernames),
            completed=0,
            failed=0,
            results={},
            started_at=datetime.now(),
            completed_at=None,
            status="running",
        )
        self.jobs[job_id] = job

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def search_username(username: str) -> None:
            async with semaphore:
                try:
                    results = await self.search_service.search_username(
                        username, exclude_nsfw=exclude_nsfw
                    )
                    job.results[username] = {
                        "status": "success",
                        "results": results,
                        "count": len(results),
                    }
                    job.completed += 1
                except Exception as e:
                    logger.error(f"Failed to search username {username}: {e}")
                    job.results[username] = {"status": "failed", "error": str(e)}
                    job.failed += 1

                if progress_callback:
                    progress_callback(job.completed + job.failed, job.total)

        tasks = [search_username(username) for username in usernames]
        await asyncio.gather(*tasks)

        job.completed_at = datetime.now()
        job.status = "completed"

        return {
            "job_id": job_id,
            "total": job.total,
            "completed": job.completed,
            "failed": job.failed,
            "results": job.results,
            "duration": (job.completed_at - job.started_at).total_seconds(),
        }

    async def process_emails(
        self,
        emails: List[str],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Process multiple emails in batch.

        Args:
            emails: List of emails to investigate
            progress_callback: Callback for progress updates

        Returns:
            Batch results
        """
        from nyx.intelligence.email import EmailIntelligence

        import uuid

        job_id = str(uuid.uuid4())
        job = BatchJob(
            id=job_id,
            queries=emails,
            total=len(emails),
            completed=0,
            failed=0,
            results={},
            started_at=datetime.now(),
            completed_at=None,
            status="running",
        )
        self.jobs[job_id] = job

        email_intel = EmailIntelligence()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def investigate_email(email: str) -> None:
            async with semaphore:
                try:
                    result = await email_intel.investigate(email)
                    job.results[email] = {
                        "status": "success",
                        "result": {
                            "valid": result.valid,
                            "breached": result.breached,
                            "breach_count": result.breach_count,
                            "reputation": result.reputation_score,
                        },
                    }
                    job.completed += 1
                except Exception as e:
                    logger.error(f"Failed to investigate email {email}: {e}")
                    job.results[email] = {"status": "failed", "error": str(e)}
                    job.failed += 1

                if progress_callback:
                    progress_callback(job.completed + job.failed, job.total)

        tasks = [investigate_email(email) for email in emails]
        await asyncio.gather(*tasks)

        job.completed_at = datetime.now()
        job.status = "completed"

        return {
            "job_id": job_id,
            "total": job.total,
            "completed": job.completed,
            "failed": job.failed,
            "results": job.results,
            "duration": (job.completed_at - job.started_at).total_seconds(),
        }

    async def process_phones(
        self,
        phones: List[str],
        region: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Process multiple phone numbers in batch.

        Args:
            phones: List of phone numbers to investigate
            region: Default region code
            progress_callback: Callback for progress updates

        Returns:
            Batch results
        """
        from nyx.intelligence.phone import PhoneIntelligence

        import uuid

        job_id = str(uuid.uuid4())
        job = BatchJob(
            id=job_id,
            queries=phones,
            total=len(phones),
            completed=0,
            failed=0,
            results={},
            started_at=datetime.now(),
            completed_at=None,
            status="running",
        )
        self.jobs[job_id] = job

        phone_intel = PhoneIntelligence()
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def investigate_phone(phone: str) -> None:
            async with semaphore:
                try:
                    result = await phone_intel.investigate(phone, region)
                    job.results[phone] = {
                        "status": "success",
                        "result": {
                            "valid": result.valid,
                            "country": result.country_name,
                            "carrier": result.carrier,
                            "reputation": result.reputation_score,
                        },
                    }
                    job.completed += 1
                except Exception as e:
                    logger.error(f"Failed to investigate phone {phone}: {e}")
                    job.results[phone] = {"status": "failed", "error": str(e)}
                    job.failed += 1

                if progress_callback:
                    progress_callback(job.completed + job.failed, job.total)

        tasks = [investigate_phone(phone) for phone in phones]
        await asyncio.gather(*tasks)

        job.completed_at = datetime.now()
        job.status = "completed"

        return {
            "job_id": job_id,
            "total": job.total,
            "completed": job.completed,
            "failed": job.failed,
            "results": job.results,
            "duration": (job.completed_at - job.started_at).total_seconds(),
        }

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get batch job by ID.

        Args:
            job_id: Job ID

        Returns:
            Batch job or None
        """
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[BatchJob]:
        """List all batch jobs.

        Returns:
            List of batch jobs
        """
        return list(self.jobs.values())

    async def aclose(self) -> None:
        """Close underlying HTTP resources.

        This should be called when the batch processor is no longer needed
        to avoid leaking open HTTP connections.
        """
        await self.search_service.aclose()