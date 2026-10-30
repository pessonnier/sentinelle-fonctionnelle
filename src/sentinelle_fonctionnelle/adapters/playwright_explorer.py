"""Adaptateur Playwright pour les plans d'exploration déclaratifs."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from sentinelle_fonctionnelle.application.rendered_page_analysis import (
    ExplorationAction,
    ExplorationLocator,
    RenderedPageAnalysisError,
    RenderedPageExplorationPlan,
    RenderedPageSnapshot,
)


@dataclass(slots=True)
class PlaywrightRenderedPageExplorer:
    base_url: str | None = None
    browser: str = "chromium"
    headless: bool = True

    def explore(
        self,
        plan: RenderedPageExplorationPlan,
        actions: tuple[ExplorationAction, ...],
    ) -> RenderedPageSnapshot:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise RenderedPageAnalysisError(
                "Playwright est absent. Installez l'extra test puis Chromium."
            ) from error

        runtime_origin = self.base_url or _origin_text(plan.start_url)
        start_url = _runtime_url(runtime_origin, plan.start_url)
        timeout_ms = plan.timeout_seconds * 1_000
        try:
            with sync_playwright() as playwright:
                browser_type = getattr(playwright, self.browser, None)
                if browser_type is None:
                    raise RenderedPageAnalysisError(
                        f"Le navigateur « {self.browser} » est inconnu."
                    )
                browser = browser_type.launch(headless=self.headless)
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(timeout_ms)
                page.set_default_navigation_timeout(timeout_ms)
                page.goto(start_url, wait_until="domcontentloaded")
                _assert_runtime_origin(page.url, runtime_origin)
                for action in actions:
                    locator = _locator(page, action.locator)
                    if action.action == "fill":
                        locator.fill(action.value)
                    elif action.action == "check":
                        locator.check()
                    elif action.action == "uncheck":
                        locator.uncheck()
                    elif action.action == "click":
                        locator.click()
                    elif action.action == "select":
                        locator.select_option(label=action.value)
                    elif action.action == "wait_visible":
                        locator.wait_for(state="visible")
                    elif action.action == "wait_hidden":
                        locator.wait_for(state="hidden")
                    else:  # Le domaine ferme déjà cette liste.
                        raise AssertionError(f"Action non gérée : {action.action}")
                    _assert_runtime_origin(page.url, runtime_origin)
                source_response = context.request.get(page.url)
                if not source_response.ok:
                    raise RenderedPageAnalysisError(
                        "Le HTML serveur de la page finale n'a pas pu être relu."
                    )
                snapshot = RenderedPageSnapshot(
                    final_url=page.url,
                    title=page.title(),
                    html=page.content(),
                    browser=self.browser,
                    source_html=source_response.text(),
                )
                context.close()
                browser.close()
                return snapshot
        except RenderedPageAnalysisError:
            raise
        except (PlaywrightTimeoutError, PlaywrightError) as error:
            raise RenderedPageAnalysisError(
                f"L'exploration Playwright a échoué sans exposer les données : {error}."
            ) from error


def _locator(page: object, locator: ExplorationLocator) -> object:
    if locator.strategy == "label":
        return page.get_by_label(locator.value, exact=True)
    if locator.strategy == "role":
        role, separator, name = locator.value.partition("|")
        if not separator or not role or not name:
            raise RenderedPageAnalysisError(
                "Un localisateur role doit respecter la syntaxe role|nom."
            )
        return page.get_by_role(role, name=name, exact=True)
    if locator.strategy == "test_id":
        return page.get_by_test_id(locator.value)
    if locator.strategy == "placeholder":
        return page.get_by_placeholder(locator.value, exact=True)
    if locator.strategy == "css":
        return page.locator(locator.value)
    raise RenderedPageAnalysisError(
        f"La stratégie « {locator.strategy} » n'est pas prise en charge."
    )


def _runtime_url(runtime_origin: str, declarative_url: str) -> str:
    parsed = urlsplit(declarative_url)
    return urljoin(runtime_origin.rstrip("/") + "/", parsed.path.lstrip("/")) + (
        f"?{parsed.query}" if parsed.query else ""
    )


def _origin_text(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _assert_runtime_origin(url: str, expected_origin: str) -> None:
    if _origin_text(url) != _origin_text(expected_origin):
        raise RenderedPageAnalysisError(
            "L'exploration a quitté l'origine locale autorisée."
        )
