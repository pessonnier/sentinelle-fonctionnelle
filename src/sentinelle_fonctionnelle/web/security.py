"""Frontières de sécurité HTTP et réseau de l'application locale.

Les contrôles sont indépendants des routeurs afin d'être testables sans base de
données ni serveur actif. Les destinations HTTP sont résolues avant connexion et
l'adresse validée est celle réellement utilisée par la socket.
"""

from __future__ import annotations

import socket
import ssl
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from ipaddress import IPv4Address, IPv6Address, ip_address
from urllib.parse import SplitResult, urljoin, urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
MAX_REDIRECTS = 5
MAX_HTML_BYTES = 2 * 1024 * 1024
IPAddress = IPv4Address | IPv6Address
Resolver = Callable[[str, int], Iterable[str]]


class DestinationRejected(ValueError):
    """La destination réseau ne respecte pas la politique locale."""


@dataclass(frozen=True, slots=True)
class ResolvedDestination:
    """Destination normalisée dont toutes les adresses ont été contrôlées."""

    url: str
    scheme: str
    hostname: str
    port: int
    addresses: tuple[IPAddress, ...]

    @property
    def origin(self) -> tuple[str, str, int]:
        return self.scheme, self.hostname.casefold(), self.port


class SameOriginMutationMiddleware(BaseHTTPMiddleware):
    """Refuse les mutations explicitement émises depuis un autre site.

    Les clients non navigateurs sans métadonnées Fetch restent acceptés pour le
    mode local et la CLI. Un navigateur fournit ``Origin``, ``Referer`` ou
    ``Sec-Fetch-Site`` sur une soumission de formulaire.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.method.upper() not in UNSAFE_METHODS:
            return await call_next(request)

        fetch_site = request.headers.get("sec-fetch-site", "").casefold()
        if fetch_site == "cross-site":
            return _cross_site_response()

        expected_origin = _request_origin(request)
        supplied_origin = request.headers.get("origin")
        if supplied_origin and _text_origin(supplied_origin) != expected_origin:
            return _cross_site_response()

        referer = request.headers.get("referer")
        if not supplied_origin and referer and _text_origin(referer) != expected_origin:
            return _cross_site_response()

        return await call_next(request)


class DestinationPolicy:
    """Valide l'origine et les adresses d'une destination d'analyse HTML."""

    def __init__(self, resolver: Resolver | None = None) -> None:
        self._resolver = resolver or _system_resolver

    def authorize(
        self,
        url: str,
        *,
        project_target: str,
        security_policy: str,
    ) -> ResolvedDestination:
        parsed = _validated_http_url(url)
        project = _validated_http_url(project_target)
        if _origin(parsed) != _origin(project):
            raise DestinationRejected(
                "La page à analyser doit appartenir à la cible web du projet."
            )

        port = parsed.port or _default_port(parsed.scheme)
        raw_addresses = tuple(self._resolver(parsed.hostname or "", port))
        if not raw_addresses:
            raise DestinationRejected(
                "Le nom de la destination ne peut pas être résolu."
            )
        try:
            addresses = tuple(
                dict.fromkeys(ip_address(value) for value in raw_addresses)
            )
        except ValueError as error:
            raise DestinationRejected(
                "La résolution de la destination a retourné une adresse invalide."
            ) from error

        policy_tokens = frozenset(security_policy.casefold().replace(",", " ").split())
        loopback_allowed = "local-loopback" in policy_tokens
        for address in addresses:
            if address.is_loopback and loopback_allowed:
                continue
            if _is_non_public(address):
                raise DestinationRejected(
                    "La destination résout vers une adresse privée ou réservée."
                )
        return ResolvedDestination(
            url=url,
            scheme=parsed.scheme.casefold(),
            hostname=parsed.hostname or "",
            port=port,
            addresses=addresses,
        )

    def assert_unchanged(
        self,
        previous: ResolvedDestination,
        *,
        project_target: str,
        security_policy: str,
    ) -> ResolvedDestination:
        """Refuse un changement de résolution au cours d'une opération."""

        current = self.authorize(
            previous.url,
            project_target=project_target,
            security_policy=security_policy,
        )
        if frozenset(current.addresses) != frozenset(previous.addresses):
            raise DestinationRejected(
                "La résolution DNS de la destination a changé pendant l’analyse."
            )
        return current


class SecurePageLoader:
    """Télécharge une page bornée en connectant uniquement une IP autorisée."""

    def __init__(
        self,
        policy: DestinationPolicy | None = None,
        *,
        timeout_seconds: float = 10,
    ) -> None:
        self.policy = policy or DestinationPolicy()
        self.timeout_seconds = timeout_seconds

    def __call__(
        self,
        url: str,
        *,
        project_target: str,
        security_policy: str,
    ) -> str:
        current_url = url
        resolved_origins: dict[tuple[str, str, int], frozenset[IPAddress]] = {}
        for redirect_index in range(MAX_REDIRECTS + 1):
            destination = self.policy.authorize(
                current_url,
                project_target=project_target,
                security_policy=security_policy,
            )
            resolved = frozenset(destination.addresses)
            previous_resolution = resolved_origins.setdefault(
                destination.origin,
                resolved,
            )
            if previous_resolution != resolved:
                raise DestinationRejected(
                    "La résolution DNS de la destination a changé pendant l’analyse."
                )
            response, connection = self._request(destination)
            try:
                if response.status in REDIRECT_STATUSES:
                    location = response.headers.get("Location", "").strip()
                    if not location:
                        raise DestinationRejected(
                            "La redirection de la page ne fournit aucune destination."
                        )
                    if redirect_index == MAX_REDIRECTS:
                        raise DestinationRejected(
                            "La page dépasse la limite de cinq redirections."
                        )
                    current_url = urljoin(current_url, location)
                    continue
                if response.status >= 400:
                    raise DestinationRejected(
                        f"La page a retourné le statut HTTP {response.status}."
                    )
                media_type = response.headers.get_content_type()
                if media_type not in {"text/html", "application/xhtml+xml"}:
                    raise DestinationRejected(
                        "La ressource retournée n’est pas une page HTML."
                    )
                content = response.read(MAX_HTML_BYTES + 1)
                if len(content) > MAX_HTML_BYTES:
                    raise DestinationRejected("La page dépasse la limite de 2 Mio.")
                charset = response.headers.get_content_charset() or "utf-8"
                return content.decode(charset, errors="replace")
            finally:
                connection.close()
        raise AssertionError("La boucle de redirection doit toujours se terminer.")

    def _request(
        self,
        destination: ResolvedDestination,
    ) -> tuple[HTTPResponse, HTTPConnection]:
        address = str(destination.addresses[0])
        if destination.scheme == "https":
            connection: HTTPConnection = _PinnedHTTPSConnection(
                destination.hostname,
                destination.port,
                pinned_address=address,
                timeout=self.timeout_seconds,
            )
        else:
            connection = _PinnedHTTPConnection(
                destination.hostname,
                destination.port,
                pinned_address=address,
                timeout=self.timeout_seconds,
            )
        parsed = urlsplit(destination.url)
        resource = parsed.path or "/"
        if parsed.query:
            resource = f"{resource}?{parsed.query}"
        connection.request(
            "GET",
            resource,
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "SentinelleFonctionnelle-page-analysis/1",
            },
        )
        return connection.getresponse(), connection


class _PinnedHTTPConnection(HTTPConnection):
    def __init__(
        self,
        host: str,
        port: int,
        *,
        pinned_address: str,
        timeout: float,
    ) -> None:
        self._pinned_address = pinned_address
        super().__init__(host, port, timeout=timeout)

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
        )


class _PinnedHTTPSConnection(HTTPSConnection):
    def __init__(
        self,
        host: str,
        port: int,
        *,
        pinned_address: str,
        timeout: float,
    ) -> None:
        self._pinned_address = pinned_address
        self._ssl_context = ssl.create_default_context()
        super().__init__(host, port, timeout=timeout, context=self._ssl_context)

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._pinned_address, self.port),
            self.timeout,
        )
        self.sock = self._ssl_context.wrap_socket(raw_socket, server_hostname=self.host)


def _system_resolver(hostname: str, port: int) -> Iterable[str]:
    return (
        str(result[4][0])
        for result in socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
        )
    )


def _validated_http_url(value: str) -> SplitResult:
    parsed = urlsplit(value.strip())
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise DestinationRejected("La page doit être une URL HTTP ou HTTPS absolue.")
    if parsed.username or parsed.password:
        raise DestinationRejected("Une URL de page ne peut contenir d’identifiants.")
    try:
        _ = parsed.port
    except ValueError as error:
        raise DestinationRejected("Le port de la destination est invalide.") from error
    return parsed


def _origin(parsed: SplitResult) -> tuple[str, str, int]:
    return (
        parsed.scheme.casefold(),
        (parsed.hostname or "").casefold(),
        parsed.port or _default_port(parsed.scheme),
    )


def _default_port(scheme: str) -> int:
    return 443 if scheme.casefold() == "https" else 80


def _is_non_public(address: IPAddress) -> bool:
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _request_origin(request: Request) -> tuple[str, str, int]:
    return _text_origin(str(request.base_url))


def _text_origin(value: str) -> tuple[str, str, int]:
    parsed = urlsplit(value)
    return (
        parsed.scheme.casefold(),
        (parsed.hostname or "").casefold(),
        parsed.port or _default_port(parsed.scheme),
    )


def _cross_site_response() -> JSONResponse:
    return JSONResponse(
        {"detail": "La mutation cross-site est refusée."},
        status_code=403,
    )
