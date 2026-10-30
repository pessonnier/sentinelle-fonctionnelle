"""Contrats courts transmis au LLM selon le mode de rédaction des étapes."""

from __future__ import annotations

from typing import Any, Mapping


AUTHORING_SKILLS: dict[str, dict[str, Any]] = {
    "form": {
        "skill": "analyze-form-test-steps",
        "source": "workflow.steps",
        "instructions": [
            "Valider chaque formulaire action et contrôle sans inventer de fait.",
            "Conserver les références HTML et les jetons de données existants.",
            "Poser une question pour toute cible, valeur ou assertion manquante.",
        ],
    },
    "step_text": {
        "skill": "analyze-step-test-narratives",
        "source": "workflow.step_narratives",
        "instructions": [
            "Respecter l’ordre et la frontière de chaque texte d’étape.",
            "Extraire contexte, action, cible, valeur et contrôle observable.",
            "Proposer plusieurs étapes seulement si un texte contient plusieurs actions.",
        ],
    },
    "scenario_text": {
        "skill": "analyze-full-test-narrative",
        "source": "workflow.scenario_narrative",
        "instructions": [
            "Segmenter le récit complet en étapes minimales et ordonnées.",
            "Signaler si le récit couvre plusieurs comportements métier.",
            "Ne résoudre les cibles qu’avec le catalogue HTML fourni.",
        ],
    },
}

AUTHORING_ASSIST_PROMPTS: dict[str, str] = {
    "form": (
        "Relis les actions et contrôles structurés. Signale les données, "
        "cibles HTML ou résultats observables manquants et propose uniquement "
        "les corrections nécessaires."
    ),
    "step_text": (
        "Analyse chaque texte d’étape séparément. Propose les étapes structurées "
        "correspondantes et pose une question quand une action, une cible, une "
        "donnée ou un contrôle n’est pas explicite."
    ),
    "scenario_text": (
        "Découpe le récit complet dans l’ordre en étapes atomiques. Pour chacune, "
        "distingue prérequis, action, donnée et contrôle observable sans inventer "
        "d’information."
    ),
}


def authoring_skill_context(workflow: Mapping[str, Any]) -> dict[str, Any]:
    mode = str(workflow.get("authoring_mode") or "form")
    contract = AUTHORING_SKILLS.get(mode, AUTHORING_SKILLS["form"])
    return {
        "mode": mode if mode in AUTHORING_SKILLS else "form",
        **contract,
        "output": (
            "Préparer uniquement des questions et opérations add/replace vers "
            "le workflow canonique ; ne jamais confirmer le cas."
        ),
    }
