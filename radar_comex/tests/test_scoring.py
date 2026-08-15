from src.classifiers.rules import classify_experience, classify_relevance
from src.models import JobPosting
from src.scoring.score import score_job


def test_score_prioritizes_cv_match_entry_level():
    job = JobPosting(
        title="Pasante comercio exterior",
        company="Empresa",
        description="Importaciones, documentacion, ingles avanzado, Microsoft Office.",
        location="Retiro, CABA",
    )
    job.relevance_classification = classify_relevance(job.merged_text())[0]
    job.experience_classification = classify_experience(job.merged_text())[0]
    job.travel_minutes = 25
    score_job(
        job,
        {
            "target_roles": ["pasantia comercio exterior"],
            "education": ["comercio internacional"],
            "strengths": ["ingles avanzado", "Microsoft Office", "manejo de documentacion"],
        },
    )
    assert job.score >= 70
