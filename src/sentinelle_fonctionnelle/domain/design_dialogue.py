"""Dialogue de conception, propositions fermées et décisions humaines.

Références : EF-004, EF-005, GEN-002.1 et ACC-007 à ACC-009.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence
from uuid import uuid4

from .workflow import WorkflowAction, WorkflowAssertion, WorkflowStep


class DesignDialogueError(ValueError):
    """Une réponse ou une décision ne respecte pas le contrat de conception."""


class OperationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    DECIDED = "decided"


_OPERATION_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_STEP_PATH = re.compile(
    r"/workflow/steps/(?P<index>[0-9]+)/"
    r"(?P<field>name|page_url|precondition|action|target|value|assertion|"
    r"assertion_target|expected|evidence)\Z"
)
_TOP_LEVEL_SCALARS = {"/objective", "/actor"}
_TOP_LEVEL_LISTS = {
    "/preconditions/-",
    "/postconditions/-",
    "/requirements/-",
    "/business_rules/-",
    "/data_sets/-",
}
_WORKFLOW_SCALARS = {"/workflow/actor_profile"}
_WORKFLOW_LISTS = {
    "/workflow/fixture_refs/-",
    "/workflow/secret_refs/-",
    "/workflow/setup/-",
    "/workflow/cleanup/-",
    "/workflow/assumptions/-",
    "/workflow/steps/-",
}


@dataclass(frozen=True, slots=True)
class DesignMessage:
    id: str
    role: str
    content: str
    created_at: datetime

    def __post_init__(self) -> None:
        if self.role not in {"user", "assistant"}:
            raise DesignDialogueError("Le rôle du message est inconnu.")
        if not self.content.strip() or len(self.content) > 4_000:
            raise DesignDialogueError(
                "Un message doit contenir entre 1 et 4 000 caractères."
            )
        if self.created_at.tzinfo is None:
            raise DesignDialogueError(
                "La date d’un message doit inclure un fuseau horaire."
            )

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DesignMessage:
        return cls(
            id=str(value["id"]),
            role=str(value["role"]),
            content=str(value["content"]),
            created_at=datetime.fromisoformat(str(value["created_at"])),
        )


@dataclass(frozen=True, slots=True)
class DesignOperation:
    id: str
    operation: str
    path: str
    value: Any
    label: str
    reason: str
    status: OperationStatus = OperationStatus.PENDING

    def __post_init__(self) -> None:
        if not _OPERATION_ID.fullmatch(self.id):
            raise DesignDialogueError(
                "L’identifiant d’une proposition doit utiliser des minuscules "
                "et des tirets."
            )
        if self.operation not in {"add", "replace"}:
            raise DesignDialogueError(
                "Une proposition doit utiliser l’opération add ou replace."
            )
        if not self.label.strip() or not self.reason.strip():
            raise DesignDialogueError(
                "Une proposition doit expliquer son libellé et sa raison."
            )
        if len(self.label) > 160 or len(self.reason) > 600:
            raise DesignDialogueError("Une proposition est trop longue.")
        _validate_operation(self.operation, self.path, self.value)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "operation": self.operation,
            "path": self.path,
            "value": self.value,
            "label": self.label,
            "reason": self.reason,
            "status": self.status.value,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DesignOperation:
        expected = {
            "id",
            "operation",
            "path",
            "value",
            "label",
            "reason",
            "status",
        }
        unexpected = set(value) - expected
        if unexpected:
            raise DesignDialogueError(
                "Champ de proposition LLM inconnu : "
                + ", ".join(sorted(unexpected))
                + "."
            )
        return cls(
            id=str(value["id"]),
            operation=str(value["operation"]),
            path=str(value["path"]),
            value=value.get("value"),
            label=str(value["label"]),
            reason=str(value["reason"]),
            status=OperationStatus(str(value.get("status") or "pending")),
        )


@dataclass(frozen=True, slots=True)
class DesignAssistantResponse:
    questions: tuple[str, ...]
    operations: tuple[DesignOperation, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DesignAssistantResponse:
        expected = {"schema_version", "questions", "operations"}
        unexpected = set(value) - expected
        if unexpected:
            raise DesignDialogueError(
                "Champ de réponse LLM inconnu : "
                + ", ".join(sorted(unexpected))
                + "."
            )
        if value.get("schema_version") != 1:
            raise DesignDialogueError(
                "La réponse LLM doit utiliser la version de schéma 1."
            )
        raw_questions = value.get("questions")
        raw_operations = value.get("operations")
        if not isinstance(raw_questions, list) or not isinstance(
            raw_operations,
            list,
        ):
            raise DesignDialogueError(
                "Les questions et opérations LLM doivent être des listes."
            )
        questions = tuple(str(question).strip() for question in raw_questions)
        if len(questions) > 8 or any(
            not question or len(question) > 500 for question in questions
        ):
            raise DesignDialogueError(
                "La réponse LLM contient trop de questions ou une question invalide."
            )
        if len(raw_operations) > 12:
            raise DesignDialogueError(
                "La réponse LLM contient plus de 12 propositions."
            )
        operations = tuple(
            DesignOperation.from_mapping(_mapping(operation))
            for operation in raw_operations
        )
        identifiers = tuple(operation.id for operation in operations)
        if len(identifiers) != len(set(identifiers)):
            raise DesignDialogueError(
                "La réponse LLM contient un identifiant de proposition dupliqué."
            )
        return cls(questions=questions, operations=operations)


@dataclass(frozen=True, slots=True)
class DesignProposal:
    id: str
    base_fingerprint: str
    questions: tuple[str, ...]
    operations: tuple[DesignOperation, ...]
    status: ProposalStatus
    created_at: datetime

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "base_fingerprint": self.base_fingerprint,
            "questions": list(self.questions),
            "operations": [operation.as_dict() for operation in self.operations],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DesignProposal:
        return cls(
            id=str(value["id"]),
            base_fingerprint=str(value["base_fingerprint"]),
            questions=tuple(str(item) for item in value["questions"]),
            operations=tuple(
                DesignOperation.from_mapping(_mapping(operation))
                for operation in value["operations"]
            ),
            status=ProposalStatus(str(value["status"])),
            created_at=datetime.fromisoformat(str(value["created_at"])),
        )


@dataclass(frozen=True, slots=True)
class DesignDialogue:
    schema_version: int
    llm_access_profile: str
    functional_intent: str
    messages: tuple[DesignMessage, ...]
    proposals: tuple[DesignProposal, ...]
    accepted_draft: dict[str, Any]
    summary: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise DesignDialogueError(
                "La version du dialogue de conception doit être 1."
            )

    @classmethod
    def empty(cls) -> DesignDialogue:
        return cls(
            schema_version=1,
            llm_access_profile="",
            functional_intent="",
            messages=(),
            proposals=(),
            accepted_draft={},
            summary="",
        )

    def with_exchange(
        self,
        *,
        user_message: str,
        response: DesignAssistantResponse,
        draft: Mapping[str, Any],
        llm_access_profile: str,
        functional_intent: str,
        now: datetime,
    ) -> DesignDialogue:
        user = DesignMessage(
            id=str(uuid4()),
            role="user",
            content=user_message.strip(),
            created_at=now,
        )
        assistant_parts = [
            (
                f"{len(response.operations)} proposition"
                f"{'s' if len(response.operations) != 1 else ''} structurée"
                f"{'s' if len(response.operations) != 1 else ''} préparée"
                f"{'s' if len(response.operations) != 1 else ''}."
            )
        ]
        if response.questions:
            assistant_parts.append(" ".join(response.questions))
        assistant = DesignMessage(
            id=str(uuid4()),
            role="assistant",
            content=" ".join(assistant_parts),
            created_at=now,
        )
        proposal = DesignProposal(
            id=str(uuid4()),
            base_fingerprint=draft_fingerprint(draft),
            questions=response.questions,
            operations=response.operations,
            status=ProposalStatus.PENDING,
            created_at=now,
        )
        return DesignDialogue(
            schema_version=1,
            llm_access_profile=llm_access_profile,
            functional_intent=functional_intent,
            messages=(*self.messages, user, assistant),
            proposals=(*self.proposals, proposal),
            accepted_draft=deepcopy(self.accepted_draft),
            summary=self.summary,
        )

    def decide(
        self,
        *,
        proposal_id: str,
        accepted_operation_ids: Sequence[str],
        draft: Mapping[str, Any],
        now: datetime,
    ) -> tuple[DesignDialogue, dict[str, Any], str]:
        proposal = next(
            (item for item in self.proposals if item.id == proposal_id),
            None,
        )
        if proposal is None:
            raise DesignDialogueError("La proposition de dialogue est inconnue.")
        if proposal.status is not ProposalStatus.PENDING:
            raise DesignDialogueError("La proposition a déjà reçu une décision.")
        if proposal.base_fingerprint != draft_fingerprint(draft):
            raise DesignDialogueError(
                "Le brouillon a été modifié depuis la proposition ; "
                "relancez le dialogue avant de décider."
            )
        accepted = set(accepted_operation_ids)
        known = {operation.id for operation in proposal.operations}
        if not accepted <= known:
            raise DesignDialogueError(
                "La décision contient une proposition inconnue."
            )
        patched = deepcopy(dict(draft))
        decided_operations: list[DesignOperation] = []
        for operation in proposal.operations:
            status = (
                OperationStatus.ACCEPTED
                if operation.id in accepted
                else OperationStatus.REJECTED
            )
            decided = replace(operation, status=status)
            decided_operations.append(decided)
            if status is OperationStatus.ACCEPTED:
                _apply_operation(patched, operation)
        summary = synthesize_description(patched)
        patched["summary"] = summary
        decided_proposal = replace(
            proposal,
            operations=tuple(decided_operations),
            status=ProposalStatus.DECIDED,
        )
        proposals = tuple(
            decided_proposal if item.id == proposal.id else item
            for item in self.proposals
        )
        decision_message = DesignMessage(
            id=str(uuid4()),
            role="assistant",
            content=(
                f"{len(accepted)} proposition"
                f"{'s' if len(accepted) != 1 else ''} acceptée"
                f"{'s' if len(accepted) != 1 else ''}. "
                "La description a été reconstruite depuis le brouillon accepté."
            ),
            created_at=now,
        )
        dialogue = DesignDialogue(
            schema_version=1,
            llm_access_profile=self.llm_access_profile,
            functional_intent=self.functional_intent,
            messages=(*self.messages, decision_message),
            proposals=proposals,
            accepted_draft=deepcopy(patched),
            summary=summary,
        )
        return dialogue, patched, summary

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "llm_access_profile": self.llm_access_profile,
            "functional_intent": self.functional_intent,
            "messages": [message.as_dict() for message in self.messages],
            "proposals": [proposal.as_dict() for proposal in self.proposals],
            "accepted_draft": deepcopy(self.accepted_draft),
            "summary": self.summary,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DesignDialogue:
        return cls(
            schema_version=int(value["schema_version"]),
            llm_access_profile=str(value.get("llm_access_profile") or ""),
            functional_intent=str(value.get("functional_intent") or ""),
            messages=tuple(
                DesignMessage.from_mapping(_mapping(message))
                for message in value.get("messages", ())
            ),
            proposals=tuple(
                DesignProposal.from_mapping(_mapping(proposal))
                for proposal in value.get("proposals", ())
            ),
            accepted_draft=deepcopy(
                dict(_mapping(value.get("accepted_draft", {})))
            ),
            summary=str(value.get("summary") or ""),
        )


def canonical_design_draft(value: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "objective",
        "actor",
        "summary",
        "preconditions",
        "postconditions",
        "requirements",
        "business_rules",
        "data_sets",
        "workflow",
    }
    unexpected = set(value) - expected
    if unexpected:
        raise DesignDialogueError(
            "Champ de brouillon inconnu : "
            + ", ".join(sorted(unexpected))
            + "."
        )
    draft = {
        "objective": _bounded_string(value.get("objective"), 500, "L’objectif"),
        "actor": _bounded_string(value.get("actor"), 200, "L’acteur"),
        "summary": _bounded_string(value.get("summary"), 1_200, "La description"),
        "preconditions": _string_list(value.get("preconditions", ())),
        "postconditions": _string_list(value.get("postconditions", ())),
        "requirements": _string_list(value.get("requirements", ())),
        "business_rules": _string_list(value.get("business_rules", ())),
        "data_sets": _string_list(value.get("data_sets", ())),
        "workflow": deepcopy(dict(_mapping(value.get("workflow")))),
    }
    serialized = json.dumps(draft, ensure_ascii=False, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > 512 * 1024:
        raise DesignDialogueError("Le brouillon de dialogue dépasse 512 Kio.")
    return draft


def draft_fingerprint(draft: Mapping[str, Any]) -> str:
    canonical = canonical_design_draft(draft)
    serialized = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def synthesize_description(draft: Mapping[str, Any]) -> str:
    """Reconstruit une description factuelle sans utiliser le texte du LLM."""

    objective = str(draft.get("objective") or "").strip()
    actor = str(draft.get("actor") or "").strip()
    preconditions = _string_list(draft.get("preconditions", ()))
    workflow = _mapping(draft.get("workflow"))
    steps = tuple(
        step
        for step in workflow.get("steps", ())
        if isinstance(step, Mapping)
    )
    sentences: list[str] = []
    if objective:
        sentences.append(_sentence(objective))
    if actor:
        sentences.append(f"Acteur : {actor}.")
    if preconditions:
        sentences.append(
            "Préconditions : " + "; ".join(preconditions) + "."
        )
    observable = next(
        (
            str(step.get("expected") or "").strip()
            for step in reversed(steps)
            if str(step.get("assertion") or "none") != "none"
            and str(step.get("expected") or "").strip()
        ),
        "",
    )
    if observable:
        sentences.append(f"Résultat attendu : {observable}.")
    return " ".join(sentences)


def _validate_operation(operation: str, path: str, value: Any) -> None:
    if path in _TOP_LEVEL_SCALARS:
        if operation != "replace":
            raise DesignDialogueError(
                f"Le chemin {path} exige une opération replace."
            )
        _bounded_string(value, 500, path)
        return
    if path in _TOP_LEVEL_LISTS:
        if operation != "add":
            raise DesignDialogueError(
                f"Le chemin {path} exige une opération add."
            )
        _bounded_string(value, 600, path, required=True)
        return
    if path in _WORKFLOW_SCALARS:
        if operation != "replace":
            raise DesignDialogueError(
                f"Le chemin {path} exige une opération replace."
            )
        reference = _bounded_string(value, 160, path, required=True)
        if not _REFERENCE.fullmatch(reference):
            raise DesignDialogueError(
                "Le profil d’acteur proposé contient un caractère interdit."
            )
        return
    if path in _WORKFLOW_LISTS:
        if operation != "add":
            raise DesignDialogueError(
                f"Le chemin {path} exige une opération add."
            )
        if path == "/workflow/steps/-":
            WorkflowStep.from_mapping(_mapping(value), 1)
            return
        text = _bounded_string(value, 600, path, required=True)
        if path in {
            "/workflow/fixture_refs/-",
            "/workflow/secret_refs/-",
        } and not _REFERENCE.fullmatch(text):
            raise DesignDialogueError(
                "Une référence proposée contient un caractère interdit."
            )
        return
    match = _STEP_PATH.fullmatch(path)
    if match is None:
        raise DesignDialogueError(
            f"Le chemin de proposition interdit : {path}."
        )
    if operation != "replace":
        raise DesignDialogueError(
            "La modification d’une étape existante exige replace."
        )
    field = match.group("field")
    if field == "action":
        WorkflowAction(str(value))
    elif field == "assertion":
        WorkflowAssertion(str(value))
    elif field == "evidence":
        if not isinstance(value, bool):
            raise DesignDialogueError("La preuve proposée doit être un booléen.")
    else:
        _bounded_string(value, 1_000, field)


def _apply_operation(draft: dict[str, Any], operation: DesignOperation) -> None:
    path = operation.path
    if path in _TOP_LEVEL_SCALARS:
        draft[path.removeprefix("/")] = deepcopy(operation.value)
        return
    if path in _TOP_LEVEL_LISTS:
        key = path.split("/")[1]
        draft.setdefault(key, []).append(deepcopy(operation.value))
        return
    workflow = draft.setdefault("workflow", {})
    if path in _WORKFLOW_SCALARS:
        workflow[path.split("/")[-1]] = deepcopy(operation.value)
        return
    if path in _WORKFLOW_LISTS:
        key = path.split("/")[2]
        workflow.setdefault(key, []).append(deepcopy(operation.value))
        return
    match = _STEP_PATH.fullmatch(path)
    if match is None:
        raise DesignDialogueError(
            f"Le chemin de proposition interdit : {path}."
        )
    index = int(match.group("index"))
    steps = workflow.get("steps")
    if not isinstance(steps, list) or index >= len(steps):
        raise DesignDialogueError(
            "La proposition vise une étape qui n’existe plus."
        )
    steps[index][match.group("field")] = deepcopy(operation.value)


def _sentence(value: str) -> str:
    normalized = value.strip()
    return normalized if normalized.endswith((".", "!", "?")) else normalized + "."


def _bounded_string(
    value: Any,
    maximum: int,
    label: str,
    *,
    required: bool = False,
) -> str:
    if not isinstance(value, str):
        raise DesignDialogueError(f"{label} doit être un texte.")
    normalized = value.strip()
    if required and not normalized:
        raise DesignDialogueError(f"{label} ne peut pas être vide.")
    if len(normalized) > maximum:
        raise DesignDialogueError(f"{label} dépasse {maximum} caractères.")
    return normalized


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise DesignDialogueError("Une liste de textes est attendue.")
    result = [
        _bounded_string(item, 600, "Une valeur de liste", required=True)
        for item in value
    ]
    if len(result) > 100:
        raise DesignDialogueError("Une liste du brouillon dépasse 100 valeurs.")
    return result


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DesignDialogueError("Un objet structuré est attendu.")
    return value
