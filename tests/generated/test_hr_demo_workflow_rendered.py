"""Généré depuis le workflow hr_demo_manager_onboarding. Ne pas modifier à la main."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from playwright.sync_api import Page, expect
import pytest

from sentinelle_fonctionnelle.adapters.tabular import parse_tabular_data


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_VERSION = '0.2.0'
DATA_SOURCES = (
    ('login', 'outputs/hr-demo/connexion-rh.xlsx', 'case_id', '88d8e9013f2ac9419e2b4c086349622293e1be8a963d90fa35a31cf6c3021377'),
    ('employee', 'outputs/hr-demo/saisie-collaborateurs.xlsx', 'case_id', '76a07fb6b9b8fcd372b326212a7d95c6fb0819e1f8d029d7ae26ba61e2b3dc38'),
)
DATA_CASES = (
    ('manager-zoe-nebuleuse', {'login': 'LOGIN-MANAGER-OK', 'employee': 'EMPLOYEE-MANAGER-01'}),
    ('manager-iris-comete', {'login': 'LOGIN-MANAGER-OK', 'employee': 'EMPLOYEE-MANAGER-02'}),
)
TOKEN = re.compile(r"\{\{data\.([A-Za-z_][A-Za-z0-9_.-]*)\}\}")


def _read_data_source(
    source_id: str,
    relative_path: str,
    key_column: str,
    expected_sha256: str,
) -> dict[str, dict[str, str]]:
    path = ROOT / relative_path
    content = path.read_bytes()
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if expected_sha256 and actual_sha256 != expected_sha256:
        raise AssertionError(
            f"Empreinte XLSX modifiée pour {source_id} : "
            f"{actual_sha256} au lieu de {expected_sha256}"
        )
    data_set = parse_tabular_data(path.name, content)
    if key_column not in data_set.headers:
        raise AssertionError(
            f"Colonne clé XLSX absente pour {source_id} : {key_column}"
        )
    key_index = data_set.headers.index(key_column)
    indexed: dict[str, dict[str, str]] = {}
    for row in data_set.rows:
        key = row[key_index]
        if not key or key in indexed:
            raise AssertionError(
                f"Clé XLSX vide ou dupliquée pour {source_id} : {key!r}"
            )
        indexed[key] = dict(zip(data_set.headers, row, strict=True))
    return indexed


def _load_data_cases() -> list[object]:
    sources = {
        source_id: _read_data_source(
            source_id,
            relative_path,
            key_column,
            expected_sha256,
        )
        for source_id, relative_path, key_column, expected_sha256 in DATA_SOURCES
    }
    parameters: list[object] = []
    for case_id, selections in DATA_CASES:
        merged: dict[str, str] = {}
        for source_id, _, _, _ in DATA_SOURCES:
            row_key = selections[source_id]
            try:
                row = sources[source_id][row_key]
            except KeyError as error:
                raise AssertionError(
                    f"Ligne XLSX absente pour {source_id} : {row_key}"
                ) from error
            merged.update(
                {
                    f"{source_id}.{column}": value
                    for column, value in row.items()
                }
            )
        parameters.append(pytest.param(merged, id=case_id))
    return parameters


def _value(template: str, data: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in data:
            raise AssertionError(f"Donnée XLSX absente : {key}")
        return data[key]

    return TOKEN.sub(replace, template)


def _target_url(base_url: str, configured_url: str) -> str:
    parsed = urlsplit(configured_url)
    suffix = parsed.path or "/"
    if parsed.query:
        suffix += "?" + parsed.query
    return base_url.rstrip("/") + suffix


def _fill(locator: object, value: str) -> None:
    input_type = locator.get_attribute("type")
    if input_type in {"color", "range"}:
        locator.evaluate(
            """(element, nextValue) => {
                element.value = nextValue;
                element.dispatchEvent(new Event("input", { bubbles: true }));
                element.dispatchEvent(new Event("change", { bubbles: true }));
            }""",
            value,
        )
        return
    locator.fill(value)


@pytest.mark.parametrize("data", _load_data_cases())
def test_manager_creates_employee_from_xlsx(page: Page, data: dict[str, str]) -> None:
    page.set_default_timeout(30000)
    base_url = os.environ.get(
        "HR_DEMO_BASE_URL",
        "http://127.0.0.1:8000",
    )


    # Ouvrir la connexion RH
    page.goto(_target_url(base_url, 'http://127.0.0.1:8000/demo/hr/login'))

    # Saisir l’adresse du manager
    _fill(page.get_by_label('Adresse professionnelle', exact=True), _value('{{data.login.email}}', data))
    expect(page.get_by_label('Adresse professionnelle', exact=True)).to_have_value(_value('{{data.login.email}}', data))

    # Saisir le mot de passe synthétique
    _fill(page.get_by_label('Mot de passe de démonstration', exact=True), _value('{{data.login.password}}', data))

    # Attendre et saisir le code JavaScript
    _fill(page.get_by_label('Code du portail astral', exact=True), _value('{{data.login.portal_code}}', data))
    expect(page.get_by_label('Code du portail astral', exact=True)).to_have_value(_value('{{data.login.portal_code}}', data))

    # Accepter la charte cosmique
    page.get_by_label('J’accepte que mon dossier soit relu par un lama syndiqué.', exact=True).check()
    expect(page.get_by_label('J’accepte que mon dossier soit relu par un lama syndiqué.', exact=True)).to_be_checked()

    # Ouvrir le sas RH
    page.get_by_role('button', name='Ouvrir le sas RH', exact=True).click()
    expect(page.get_by_role('heading', name='Déclarer un nouveau talent', exact=True)).to_be_visible()

    # Saisir le matricule
    _fill(page.get_by_label('Matricule', exact=True), _value('{{data.employee.employee_number}}', data))
    expect(page.get_by_label('Matricule', exact=True)).to_have_value(_value('{{data.employee.employee_number}}', data))

    # Saisir le prénom
    _fill(page.get_by_label('Prénom', exact=True), _value('{{data.employee.first_name}}', data))

    # Saisir le nom
    _fill(page.get_by_label('Nom', exact=True), _value('{{data.employee.last_name}}', data))

    # Saisir l’e-mail professionnel
    _fill(page.get_by_label('E-mail professionnel', exact=True), _value('{{data.employee.work_email}}', data))

    # Saisir la date d’arrivée
    _fill(page.get_by_label('Date d’arrivée', exact=True), _value('{{data.employee.hire_date}}', data))

    # Choisir la constellation
    page.get_by_label('Constellation de rattachement', exact=True).select_option(label=_value('{{data.employee.department}}', data))
    expect(page.get_by_label('Constellation de rattachement', exact=True)).to_have_value(_value('{{data.employee.department}}', data))

    # Choisir le contrat
    page.get_by_label('CDI intersidéral', exact=True).check()
    expect(page.get_by_label('CDI intersidéral', exact=True)).to_be_checked()

    # Saisir le champ HTML médiocre
    _fill(page.get_by_test_id('animal-totem'), _value('{{data.employee.animal_totem}}', data))
    expect(page.get_by_test_id('animal-totem')).to_have_value(_value('{{data.employee.animal_totem}}', data))

    # Saisir le champ réservé au manager
    _fill(page.get_by_label('Budget d’accueil autorisé', exact=True), _value('{{data.employee.manager_budget}}', data))

    # Saisir la directive du manager
    _fill(page.get_by_label('Directive secrètement non secrète du manager', exact=True), _value('{{data.employee.manager_comment}}', data))

    # Saisir la couleur générée par JavaScript
    _fill(page.get_by_label('Couleur d’aura préférée', exact=True), _value('{{data.employee.favorite_color}}', data))
    expect(page.get_by_label('Couleur d’aura préférée', exact=True)).to_have_value(_value('{{data.employee.favorite_color}}', data))

    # Saisir le niveau de panache JavaScript
    _fill(page.get_by_label('Niveau de panache', exact=True), _value('{{data.employee.energy_level}}', data))
    expect(page.get_by_label('Niveau de panache', exact=True)).to_have_value(_value('{{data.employee.energy_level}}', data))

    # Saisir les jours de téléportation
    _fill(page.get_by_label('Jours de téléportation par semaine', exact=True), _value('{{data.employee.remote_days}}', data))
    expect(page.get_by_label('Jours de téléportation par semaine', exact=True)).to_have_value(_value('{{data.employee.remote_days}}', data))

    # Saisir le composant personnalisé
    _fill(page.get_by_label('Compétences séparées par une virgule', exact=True), _value('{{data.employee.skills}}', data))
    expect(page.get_by_label('Compétences séparées par une virgule', exact=True)).to_have_value(_value('{{data.employee.skills}}', data))

    # Enregistrer le collaborateur
    page.get_by_role('button', name='Propulser le dossier', exact=True).click()
    expect(page.locator('#record-title')).to_contain_text(_value('{{data.employee.expected_title}}', data))

    # Contrôler le matricule affiché
    expect(page.locator('[data-field="employee_number"]')).to_contain_text(_value('{{data.employee.employee_number}}', data))

    # Contrôler la synthèse JavaScript
    expect(page.locator('#js-result-cards')).to_contain_text(_value('{{data.employee.energy_level}} / 100', data))
