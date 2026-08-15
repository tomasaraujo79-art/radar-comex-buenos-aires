from __future__ import annotations

import re
import unicodedata


def normalize(text: str) -> str:
    cleaned = unicodedata.normalize("NFKD", text or "")
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", cleaned.lower()).strip()


DIRECT_COMEX_PATTERNS = [
    r"\bcomercio exterior\b",
    r"\bcomercio internacional\b",
    r"\bcomex\b",
    r"\bimportaci[oó]n(?:es)?\b",
    r"\bexportaci[oó]n(?:es)?\b",
    r"\bimport\b",
    r"\bexport\b",
    r"\baduana\b",
    r"\baduanero\b",
    r"\bdespachante\b",
    r"\bfreight forwarding\b",
    r"\bforwarder\b",
    r"\bocean import\b",
    r"\bairfreight\b",
    r"\bimport operations\b",
    r"\bexport operations\b",
    r"\bcustomer service import\b",
    r"\bcustomer service export\b",
    r"\blogistica internacional\b",
    r"\bsupply chain internacional\b",
]

ADJACENT_PATTERNS = [
    r"\blogistica\b",
    r"\bsupply chain\b",
    r"\bcompras internacionales\b",
    r"\boperaciones\b",
    r"\bshipping\b",
    r"\bshipments?\b",
    r"\bembarques?\b",
    r"\bdespachantes?\b",
    r"\bproveedores internacionales\b",
    r"\bcourier\b",
    r"\biata\b",
]

NO_EXPERIENCE_PATTERNS = [
    r"\bsin experiencia\b",
    r"\bno requiere experiencia\b",
    r"\bno se requiere experiencia\b",
    r"\bprimer empleo\b",
    r"\bganas de aprender\b",
    r"\bentry[- ]level\b",
    r"\bfirst job\b",
]

NON_EXCLUDING_EXPERIENCE_PATTERNS = [
    r"\bexperiencia deseable\b",
    r"\bdeseable experiencia\b",
    r"\bexperiencia no excluyente\b",
    r"\bno excluyente\b",
    r"\bse valorara experiencia\b",
    r"\bse valora experiencia\b",
    r"\bexperience is a plus\b",
    r"\bexperience.*plus\b",
]

REQUIRES_EXPERIENCE_PATTERNS = [
    r"\bexperiencia comprobable\b",
    r"\bexperiencia excluyente\b",
    r"\bexperiencia minima\b",
    r"\bminimo\s+\d+\s+(?:ano|anos|año|años|years?)\b",
    r"\b\d+\+?\s+(?:ano|anos|año|años|years?)\s+de experiencia\b",
    r"\b\d+\+?\s+years? of experience\b",
    r"\bal menos\s+\d+\s+(?:ano|anos|año|años)\b",
    r"\brequires experience\b",
]

ENTRY_LEVEL_PATTERNS = [
    r"\bjunior\b",
    r"\bjr\b",
    r"\btrainee\b",
    r"\bpasante\b",
    r"\bpasantia\b",
    r"\bintern\b",
    r"\binternship\b",
    r"\bpracticas\b",
    r"\bprácticas\b",
]

SENIORITY_REJECT_PATTERNS = [
    r"\bsenior\b",
    r"\bsr\b",
    r"\bsemi senior\b",
    r"\bsemisenior\b",
    r"\bcoordinador\b",
    r"\bsupervisor\b",
    r"\bjefe\b",
    r"\bgerente\b",
    r"\bmanager\b",
]


def any_pattern(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def classify_relevance(text: str) -> tuple[str, list[str]]:
    clean = normalize(text)
    reasons: list[str] = []
    if any_pattern(DIRECT_COMEX_PATTERNS, clean):
        reasons.append("Relacionado directamente con Comercio Exterior, importaciones/exportaciones o aduana.")
        return "DIRECT_COMEX", reasons
    if any_pattern(ADJACENT_PATTERNS, clean):
        reasons.append("Relacionado con logística, operaciones, compras internacionales o embarques.")
        return "ADJACENT", reasons
    reasons.append("No se detecta relación suficiente con Comercio Exterior o logística internacional.")
    return "UNRELATED", reasons


def classify_experience(text: str) -> tuple[str, str]:
    clean = normalize(text)
    if any_pattern(NO_EXPERIENCE_PATTERNS, clean):
        return "SIN_EXPERIENCIA", "El aviso indica que no requiere experiencia o enfatiza aprendizaje."
    if any_pattern(NON_EXCLUDING_EXPERIENCE_PATTERNS, clean):
        return "EXPERIENCIA_NO_EXCLUYENTE", "La experiencia aparece como deseable/no excluyente."
    if any_pattern(REQUIRES_EXPERIENCE_PATTERNS, clean):
        return "REQUIERE_EXPERIENCIA", "El aviso exige experiencia previa comprobable o mínima."
    if any_pattern(SENIORITY_REJECT_PATTERNS, clean) and not any_pattern(ENTRY_LEVEL_PATTERNS, clean):
        return "REQUIERE_EXPERIENCIA", "La seniority del aviso sugiere trayectoria previa."
    return "NO_ESPECIFICA_EXPERIENCIA", "El aviso no especifica experiencia previa obligatoria."


def is_entry_level(text: str) -> bool:
    return any_pattern(ENTRY_LEVEL_PATTERNS, normalize(text))
