import logging


logger = logging.getLogger(__name__)


def job_matches_filter(job: dict, filter_doc: dict) -> bool:
    if not filter_doc.get("active", False):
        return False

    filter_source = filter_doc.get("source")
    if filter_source and job.get("source") != filter_source:
        return False

    filter_level = filter_doc.get("level")
    if filter_level and job.get("level") != filter_level:
        return False

    filter_stack = filter_doc.get("stack", [])
    if filter_stack:
        job_text = " ".join([
            str(job.get("title") or ""),
            str(job.get("description") or ""),
        ]).lower()

        for stack_item in filter_stack:
            if stack_item.lower() not in job_text:
                return False

    return True