from app.utils import normalize_url, build_dedup_key


def test_normalize_url_removes_query_params():
    url = "https://jobs.dou.ua/companies/test/vacancies/123/?from=list&utm_source=x"

    normalized = normalize_url(url)

    assert normalized == "https://jobs.dou.ua/companies/test/vacancies/123/"


def test_build_dedup_key_uses_source_and_normalized_url():
    url = "https://jobs.dou.ua/companies/test/vacancies/123/?from=list"

    dedup_key = build_dedup_key("dou", url)

    assert dedup_key == "dou:https://jobs.dou.ua/companies/test/vacancies/123/"