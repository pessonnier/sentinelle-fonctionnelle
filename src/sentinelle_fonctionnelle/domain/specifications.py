"""Définition canonique de tests saisissables sous plusieurs formes.

Références : EF-007, EF-007.4, ACC-063 et ACC-064.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .workflow import GenerationWorkflowInput, WorkflowAssertion


class SpecificationError(ValueError):
    """La saisie fonctionnelle ne peut pas produire un modèle valide."""


class SpecificationStyle(StrEnum):
    STEPS = "steps"
    GHERKIN = "gherkin"
    EXAMPLES = "examples"
    CHECKLIST = "checklist"

    @property
    def label(self) -> str:
        return {
            self.STEPS: "Pas-à-pas",
            self.GHERKIN: "Given/When/Then",
            self.EXAMPLES: "Tableau d’exemples",
            self.CHECKLIST: "Checklist",
        }[self]


class OrganizationView(StrEnum):
    TREE = "tree"
    TAG = "tag"
    REQUIREMENT = "requirement"
    BUSINESS_RULE = "business_rule"
    STYLE = "style"

    @property
    def label(self) -> str:
        return {
            self.TREE: "Arbre",
            self.TAG: "Tags",
            self.REQUIREMENT: "Exigences",
            self.BUSINESS_RULE: "Règles métier",
            self.STYLE: "Modes de spécification",
        }[self]


@dataclass(frozen=True, slots=True)
class SpecificationClause:
    keyword: str
    text: str
    expected_result: str | None = None


@dataclass(frozen=True, slots=True)
class FunctionalTestSpecification:
    """Version structurée commune aux quatre aides de rédaction."""

    style: SpecificationStyle
    version: int
    objective: str
    actor: str
    source_text: str
    environment: str
    preconditions: tuple[str, ...]
    data_sets: tuple[str, ...]
    postconditions: tuple[str, ...]
    requirements: tuple[str, ...]
    business_rules: tuple[str, ...]
    execution_declaration: tuple[str, ...]
    clauses: tuple[SpecificationClause, ...]
    example_headers: tuple[str, ...] = ()
    example_rows: tuple[tuple[str, ...], ...] = ()
    workflow: GenerationWorkflowInput | None = None
    summary: str = ""

    @classmethod
    def create(
        cls,
        *,
        style: SpecificationStyle,
        version: int,
        objective: str,
        actor: str,
        source_text: str,
        environment: str = "",
        preconditions: tuple[str, ...] = (),
        data_sets: tuple[str, ...] = (),
        postconditions: tuple[str, ...] = (),
        requirements: tuple[str, ...] = (),
        business_rules: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
        workflow: GenerationWorkflowInput | None = None,
        summary: str = "",
    ) -> FunctionalTestSpecification:
        normalized_style = SpecificationStyle(style)
        if workflow is None:
            normalized_source = _required(
                source_text,
                "Le contenu de la spécification",
            )
            clauses, headers, rows = _parse(normalized_style, normalized_source)
        else:
            normalized_style = SpecificationStyle.STEPS
            normalized_source = "\n".join(
                f"{step.action_text} => {step.assertion_text}"
                for step in workflow.steps
            )
            clauses = tuple(
                SpecificationClause(
                    keyword="ACTION",
                    text=step.action_text,
                    expected_result=(
                        step.assertion_text
                        if step.assertion is not WorkflowAssertion.NONE
                        else None
                    ),
                )
                for step in workflow.steps
            )
            headers, rows = (), ()
        declarations = _values(execution_declaration)
        allowed_declarations = {
            "on_commit",
            "on_merge_request",
            "nightly",
            "release",
            "manual",
        }
        invalid = set(declarations) - allowed_declarations
        if invalid:
            raise SpecificationError(
                "Déclaration d’exécution inconnue : "
                + ", ".join(sorted(invalid))
            )
        if version < 1:
            raise SpecificationError("La version doit être supérieure ou égale à 1.")
        return cls(
            style=normalized_style,
            version=version,
            objective=_required(objective, "L’objectif"),
            actor=_required(actor, "L’acteur"),
            source_text=normalized_source,
            environment=environment.strip(),
            preconditions=_values(preconditions),
            data_sets=_values(data_sets),
            postconditions=_values(postconditions),
            requirements=_values(requirements),
            business_rules=_values(business_rules),
            execution_declaration=declarations,
            clauses=clauses,
            example_headers=headers,
            example_rows=rows,
            workflow=workflow,
            summary=summary.strip(),
        )

    @property
    def searchable_text(self) -> str:
        values = (
            self.style.label,
            self.objective,
            self.actor,
            self.source_text,
            self.environment,
            self.summary,
            *self.preconditions,
            *self.data_sets,
            *self.postconditions,
            *self.requirements,
            *self.business_rules,
            *self.execution_declaration,
        )
        return " ".join(values).casefold()


def _parse(
    style: SpecificationStyle,
    source_text: str,
) -> tuple[
    tuple[SpecificationClause, ...],
    tuple[str, ...],
    tuple[tuple[str, ...], ...],
]:
    lines = tuple(line.strip() for line in source_text.splitlines() if line.strip())
    if style is SpecificationStyle.STEPS:
        clauses: list[SpecificationClause] = []
        for line in lines:
            parts = line.replace("=>", "→").split("→", maxsplit=1)
            if len(parts) != 2 or not all(part.strip() for part in parts):
                raise SpecificationError(
                    "Chaque étape doit utiliser « action => résultat observable »."
                )
            clauses.append(
                SpecificationClause(
                    keyword="ACTION",
                    text=parts[0].strip(),
                    expected_result=parts[1].strip(),
                )
            )
        return _at_least_one(clauses, "Une étape est obligatoire."), (), ()

    if style is SpecificationStyle.GHERKIN:
        keyword_aliases = (
            ("ÉTANT DONNÉ", "GIVEN"),
            ("ETANT DONNE", "GIVEN"),
            ("GIVEN", "GIVEN"),
            ("QUAND", "WHEN"),
            ("WHEN", "WHEN"),
            ("ALORS", "THEN"),
            ("THEN", "THEN"),
            ("ET", "AND"),
            ("AND", "AND"),
        )
        clauses = []
        previous_keyword = ""
        for line in lines:
            folded = line.upper()
            match = next(
                (
                    (prefix, canonical)
                    for prefix, canonical in keyword_aliases
                    if folded == prefix or folded.startswith(prefix + " ")
                ),
                None,
            )
            if match is None:
                raise SpecificationError(
                    "Chaque ligne BDD doit commencer par Étant donné, Quand, "
                    "Alors ou Et."
                )
            prefix, keyword = match
            text = line[len(prefix) :].strip()
            if not text:
                raise SpecificationError("Une clause BDD ne peut pas être vide.")
            effective = previous_keyword if keyword == "AND" else keyword
            if keyword != "AND":
                previous_keyword = keyword
            clauses.append(
                SpecificationClause(
                    keyword=keyword,
                    text=text,
                    expected_result=text if effective == "THEN" else None,
                )
            )
        effective_keywords: list[str] = []
        previous = ""
        for clause in clauses:
            current = previous if clause.keyword == "AND" else clause.keyword
            effective_keywords.append(current)
            if clause.keyword != "AND":
                previous = clause.keyword
        if not {"GIVEN", "WHEN", "THEN"}.issubset(effective_keywords):
            raise SpecificationError(
                "Un scénario BDD exige au moins Given, When et Then."
            )
        return tuple(clauses), (), ()

    if style is SpecificationStyle.EXAMPLES:
        parsed_rows = tuple(
            tuple(cell.strip() for cell in line.split(";")) for line in lines
        )
        if len(parsed_rows) < 2 or len(parsed_rows[0]) < 2:
            raise SpecificationError(
                "Le tableau exige un en-tête d’au moins deux colonnes et un exemple."
            )
        width = len(parsed_rows[0])
        if any(len(row) != width or any(not cell for cell in row) for row in parsed_rows):
            raise SpecificationError(
                "Toutes les lignes du tableau doivent avoir le même nombre "
                "de cellules non vides."
            )
        return (), parsed_rows[0], parsed_rows[1:]

    clauses = tuple(
        SpecificationClause(
            keyword="CHECK",
            text=line,
            expected_result=line,
        )
        for line in lines
    )
    return _at_least_one(clauses, "La checklist doit contenir un contrôle."), (), ()


def _at_least_one(
    clauses: list[SpecificationClause] | tuple[SpecificationClause, ...],
    message: str,
) -> tuple[SpecificationClause, ...]:
    if not clauses:
        raise SpecificationError(message)
    return tuple(clauses)


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise SpecificationError(f"{label} est obligatoire.")
    return normalized


def _values(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(value.strip() for value in values)
    if any(not value for value in normalized):
        raise SpecificationError("Une liste ne peut pas contenir de valeur vide.")
    return normalized
