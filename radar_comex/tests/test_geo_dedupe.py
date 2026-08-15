from src.deduplication.dedupe import assign_duplicate_hash
from src.geolocation.router import estimate_route_for_job
from src.models import JobPosting


def test_route_estimate_from_belgrano_to_retiro_under_hour():
    job = JobPosting(title="Pasante", location="Retiro, CABA")
    route = estimate_route_for_job(job, "Belgrano, CABA, Argentina")
    assert route.travel_minutes is not None
    assert route.travel_minutes <= 60


def test_duplicate_hash_same_title_company_location():
    a = JobPosting(title="Analista Jr Comex", company="ACME", location="CABA")
    b = JobPosting(title="Analista Comex", company="ACME", location="CABA")
    assign_duplicate_hash(a)
    assign_duplicate_hash(b)
    assert a.duplicate_hash == b.duplicate_hash
