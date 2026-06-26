import logging
import requests


logger = logging.getLogger(__name__)


def send_discord_job_alert(webhook_url: str, job: dict) -> int:
    payload = {
        "content": (
            f"New job match:\n"
            f"**{job.get('title', 'No title')}**\n"
            f"Company: {job.get('company') or 'Unknown'}\n"
            f"Source: {job.get('source') or 'Unknown'}\n"
            f"{job.get('link')}"
        )
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.status_code
    except requests.RequestException:
        logger.exception(
            "discord_webhook: failed for job_id=%s",
            job.get("_id"),
        )
        raise