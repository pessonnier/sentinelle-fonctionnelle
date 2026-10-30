"""Analyse HTML bornée pour proposer les champs manipulables d’une page."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
import re
import unicodedata

from sentinelle_fonctionnelle.domain.workflow import (
    AnalyzedPage,
    PageElement,
    PageLocator,
)


@dataclass(slots=True)
class _Candidate:
    kind: str
    attributes: dict[str, str]
    text: list[str] = field(default_factory=list)
    label: str = ""
    options: list[str] = field(default_factory=list)


class _PageFieldParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.candidates: list[_Candidate] = []
        self.explicit_labels: dict[str, str] = {}
        self._label: dict[str, object] | None = None
        self._text_candidate: int | None = None
        self._select_candidate: int | None = None
        self._option_parts: list[str] | None = None
        self._suppressed_label_tags: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if self._suppressed_label_tags:
            if tag == "summary" and self._label is not None:
                help_title = attributes.get("aria-label", "")
                prefix = "Informations :"
                if help_title.startswith(prefix):
                    self._label["parts"].append(help_title.removeprefix(prefix).strip())
            if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
                self._suppressed_label_tags.append(tag)
            return
        if (
            tag == "details"
            and "information-disclosure" in attributes.get("class", "").split()
        ):
            self._suppressed_label_tags.append(tag)
            return
        if tag == "title":
            self.in_title = True
            return
        if tag == "label":
            self._label = {
                "for": attributes.get("for", ""),
                "parts": [],
                "controls": [],
            }
            return
        if tag == "input":
            input_type = attributes.get("type", "text").casefold()
            if input_type in {"hidden", "reset"}:
                return
            self._append_candidate("input", attributes)
            return
        if tag in {"textarea", "select"}:
            index = self._append_candidate(tag, attributes)
            if tag == "select":
                self._select_candidate = index
            return
        if tag in {"button", "a", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._text_candidate = self._append_candidate(tag, attributes)
            return
        if tag == "option" and self._select_candidate is not None:
            self._option_parts = []

    def handle_endtag(self, tag: str) -> None:
        if self._suppressed_label_tags:
            if tag == self._suppressed_label_tags[-1]:
                self._suppressed_label_tags.pop()
            return
        if tag == "title":
            self.in_title = False
        elif tag == "label" and self._label is not None:
            label = _clean(" ".join(self._label["parts"]))
            target = str(self._label["for"])
            if target and label:
                self.explicit_labels[target] = label
            for index in self._label["controls"]:
                self.candidates[int(index)].label = label
            self._label = None
        elif tag == "option" and self._option_parts is not None:
            option = _clean(" ".join(self._option_parts))
            if option and self._select_candidate is not None:
                self.candidates[self._select_candidate].options.append(option)
            self._option_parts = None
        elif tag == "select":
            self._select_candidate = None
        elif tag in {"button", "a", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._text_candidate = None

    def handle_data(self, data: str) -> None:
        normalized = _clean(data)
        if not normalized:
            return
        if self._suppressed_label_tags:
            return
        if self.in_title:
            self.title_parts.append(normalized)
        if self._label is not None:
            self._label["parts"].append(normalized)
        if self._text_candidate is not None:
            self.candidates[self._text_candidate].text.append(normalized)
        if self._option_parts is not None:
            self._option_parts.append(normalized)

    def _append_candidate(self, kind: str, attributes: dict[str, str]) -> int:
        index = len(self.candidates)
        self.candidates.append(_Candidate(kind=kind, attributes=attributes))
        if self._label is not None:
            self._label["controls"].append(index)
        return index


def analyze_html_page(url: str, html: str) -> AnalyzedPage:
    """Retourne uniquement les éléments utiles à une action ou une assertion."""

    parser = _PageFieldParser()
    parser.feed(html)
    page_key = _slug(_last_path_part(url) or "page")
    used_references: set[str] = set()
    elements: list[PageElement] = []
    for index, candidate in enumerate(parser.candidates, start=1):
        attributes = candidate.attributes
        element_id = attributes.get("id", "")
        explicit_label = parser.explicit_labels.get(element_id, "")
        has_label = bool(explicit_label or candidate.label)
        text = _clean(" ".join(candidate.text))
        label = (
            explicit_label
            or candidate.label
            or attributes.get("aria-label", "")
            or text
            or attributes.get("placeholder", "")
            or attributes.get("name", "")
            or element_id
            or f"{candidate.kind} {index}"
        )
        label = _clean(label)
        role, input_type = _role(candidate.kind, attributes)
        reference_key = _slug(
            attributes.get("name")
            or element_id
            or label
            or f"element-{index}"
        )
        reference = f"page:{page_key}#{reference_key}"
        suffix = 2
        while reference in used_references:
            reference = f"page:{page_key}#{reference_key}-{suffix}"
            suffix += 1
        used_references.add(reference)
        elements.append(
            PageElement(
                reference=reference,
                kind=candidate.kind,
                role=role,
                label=label,
                input_type=input_type,
                locator=_locator(candidate, label, role, has_label=has_label),
                options=tuple(candidate.options),
            )
        )
    return AnalyzedPage(
        url=url,
        title=_clean(" ".join(parser.title_parts)),
        fingerprint=sha256(html.encode("utf-8")).hexdigest(),
        elements=tuple(elements),
    )


def _locator(
    candidate: _Candidate,
    label: str,
    role: str,
    *,
    has_label: bool,
) -> PageLocator:
    attributes = candidate.attributes
    if has_label:
        return PageLocator("label", label)
    if candidate.kind in {"button", "a", "h1", "h2", "h3", "h4", "h5", "h6"}:
        return PageLocator("role", f"{role}|{label}")
    if attributes.get("aria-label"):
        return PageLocator("role", f"{role}|{label}")
    if attributes.get("data-testid"):
        return PageLocator("test_id", attributes["data-testid"])
    if attributes.get("placeholder"):
        return PageLocator("placeholder", attributes["placeholder"])
    if attributes.get("name"):
        return PageLocator("css", f'[name="{attributes["name"]}"]')
    return PageLocator("css", f"#{attributes['id']}")


def _role(kind: str, attributes: dict[str, str]) -> tuple[str, str]:
    input_type = attributes.get("type", "text").casefold() if kind == "input" else ""
    if kind == "input":
        if input_type in {"submit", "button"}:
            return "button", input_type
        if input_type == "checkbox":
            return "checkbox", input_type
        if input_type == "radio":
            return "radio", input_type
        if input_type == "number":
            return "spinbutton", input_type
        return "textbox", input_type
    return {
        "textarea": ("textbox", "textarea"),
        "select": ("combobox", "select"),
        "button": ("button", attributes.get("type", "button")),
        "a": ("link", "link"),
        "h1": ("heading", "heading"),
        "h2": ("heading", "heading"),
        "h3": ("heading", "heading"),
        "h4": ("heading", "heading"),
        "h5": ("heading", "heading"),
        "h6": ("heading", "heading"),
    }[kind]


def _last_path_part(url: str) -> str:
    path = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    return path.split("#", 1)[0]


def _slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return normalized or "element"


def _clean(value: str) -> str:
    return " ".join(value.split())
