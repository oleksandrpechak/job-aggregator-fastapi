from bs4 import BeautifulSoup

from app.tasks import parse_dou_listing


BASE_URL = "https://jobs.dou.ua/vacancies/?category=Python"


def test_parse_dou_listing_from_saved_html_fixture():
    with open("app/tests/fixtures/dou_jobs.html", encoding="utf-8") as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")
    item = soup.select_one(".l-vacancy")

    job = parse_dou_listing(
        item=item,
        base_url=BASE_URL,
        source="dou",
        source_name="dou_python",
    )

    assert job is not None
    assert job["title"] == "Junior Python FastAPI Developer"
    assert job["company"] == "Test Company"
    assert job["source"] == "dou"
    assert job["source_name"] == "dou_python"
    assert job["link"] == "https://jobs.dou.ua/companies/test-company/vacancies/12345/"
    assert job["dedup_key"] == "dou:https://jobs.dou.ua/companies/test-company/vacancies/12345/"
    assert job["posted_at"] is not None
    assert job["scraped_at"] is not None


def test_parse_dou_listing_returns_none_when_link_missing():
    html = """
    <li class="l-vacancy">
      <div class="title">Junior Python Developer</div>
      <div class="company">Broken Company</div>
      <div class="date">16 червня</div>
    </li>
    """

    soup = BeautifulSoup(html, "html.parser")
    item = soup.select_one(".l-vacancy")

    job = parse_dou_listing(
        item=item,
        base_url=BASE_URL,
        source="dou",
        source_name="dou_python",
    )

    assert job is None