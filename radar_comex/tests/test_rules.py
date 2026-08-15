from src.classifiers.rules import classify_experience, classify_relevance


def test_direct_comex_and_no_experience():
    text = "Pasantia comercio exterior, importaciones. No requiere experiencia."
    assert classify_relevance(text)[0] == "DIRECT_COMEX"
    assert classify_experience(text)[0] == "SIN_EXPERIENCIA"


def test_rejects_required_experience():
    text = "Analista senior de importaciones con 3 años de experiencia comprobable."
    assert classify_experience(text)[0] == "REQUIERE_EXPERIENCIA"
