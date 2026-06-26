from app.services.matching import job_matches_filter


def test_matches_when_all_conditions_pass():
    job = {
        "title": "Junior Python FastAPI Developer",
        "description": "MongoDB and Redis experience is a plus",
        "level": "junior",
        "source": "dou",
    }

    filter_doc = {
        "level": "junior",
        "stack": ["python", "fastapi"],
        "source": "dou",
        "active": True,
    }

    assert job_matches_filter(job, filter_doc) is True


def test_does_not_match_inactive_filter():
    job = {
        "title": "Junior Python Developer",
        "level": "junior",
        "source": "dou",
    }

    filter_doc = {
        "level": "junior",
        "stack": ["python"],
        "source": "dou",
        "active": False,
    }

    assert job_matches_filter(job, filter_doc) is False


def test_does_not_match_wrong_source():
    job = {
        "title": "Junior Python Developer",
        "level": "junior",
        "source": "djinni",
    }

    filter_doc = {
        "level": "junior",
        "stack": ["python"],
        "source": "dou",
        "active": True,
    }

    assert job_matches_filter(job, filter_doc) is False


def test_does_not_match_wrong_level():
    job = {
        "title": "Senior Python Developer",
        "level": "senior",
        "source": "dou",
    }

    filter_doc = {
        "level": "junior",
        "stack": ["python"],
        "source": "dou",
        "active": True,
    }

    assert job_matches_filter(job, filter_doc) is False


def test_empty_stack_means_no_stack_restriction():
    job = {
        "title": "Junior Backend Developer",
        "level": "junior",
        "source": "dou",
    }

    filter_doc = {
        "level": "junior",
        "stack": [],
        "source": "dou",
        "active": True,
    }

    assert job_matches_filter(job, filter_doc) is True


def test_does_not_match_when_one_stack_item_missing():
    job = {
        "title": "Junior Python Developer",
        "description": "Django experience",
        "level": "junior",
        "source": "dou",
    }

    filter_doc = {
        "level": "junior",
        "stack": ["python", "fastapi"],
        "source": "dou",
        "active": True,
    }

    assert job_matches_filter(job, filter_doc) is False