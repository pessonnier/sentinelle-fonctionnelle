"""Application de démonstration multi-écrans pour la conception de tests."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from threading import Lock
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates


@dataclass(frozen=True, slots=True)
class DemoProduct:
    code: str
    name: str
    category: str
    price: Decimal
    stock: int


PRODUCTS = (
    DemoProduct(
        "CLAV-01", "Clavier mécanique azur", "Périphériques", Decimal("89.90"), 12
    ),
    DemoProduct("ECR-27", "Écran 27 pouces", "Écrans", Decimal("249.00"), 6),
    DemoProduct("SUP-USB", "Station USB-C", "Accessoires", Decimal("74.50"), 18),
    DemoProduct("CAS-RED", "Casque rouge", "Audio", Decimal("59.90"), 9),
)

_DRAFTS: dict[str, dict[str, Any]] = {}
_ORDERS: dict[str, dict[str, Any]] = {}
_LOCK = Lock()


def build_orders_demo_router(templates: Jinja2Templates) -> APIRouter:
    router = APIRouter(prefix="/demo/commandes", tags=["cible-commandes-demo"])

    @router.get("", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse("/demo/commandes/client", status_code=303)

    @router.get("/client", response_class=HTMLResponse)
    def client_page(request: Request) -> HTMLResponse:
        return _render_client(templates, request)

    @router.post("/client")
    def create_client_draft(
        request: Request,
        customer_name: str = Form(),
        email: str = Form(),
        customer_type: str = Form(),
        requested_date: str = Form(),
        priority: str = Form(),
        notes: str = Form(""),
    ) -> Response:
        values = {
            "customer_name": customer_name.strip(),
            "email": email.strip(),
            "customer_type": customer_type.strip(),
            "requested_date": requested_date.strip(),
            "priority": priority.strip(),
            "notes": notes.strip(),
        }
        if not all(
            values[key]
            for key in (
                "customer_name",
                "email",
                "customer_type",
                "requested_date",
                "priority",
            )
        ):
            return _render_client(
                templates,
                request,
                values=values,
                error="Tous les champs obligatoires doivent être renseignés.",
                status_code=400,
            )
        draft_id = uuid4().hex[:10]
        with _LOCK:
            _DRAFTS[draft_id] = {
                **values,
                "quantities": {},
                "delivery_mode": "standard",
                "discount_code": "",
                "gift_wrap": False,
            }
        return RedirectResponse(f"/demo/commandes/articles/{draft_id}", status_code=303)

    @router.get("/articles/{draft_id}", response_class=HTMLResponse)
    def items_page(request: Request, draft_id: str) -> Response:
        draft = _draft(draft_id)
        if draft is None:
            return RedirectResponse("/demo/commandes/client", status_code=303)
        return _render_items(templates, request, draft_id, draft)

    @router.post("/articles/{draft_id}")
    async def save_items(request: Request, draft_id: str) -> Response:
        draft = _draft(draft_id)
        if draft is None:
            return RedirectResponse("/demo/commandes/client", status_code=303)
        form = await request.form()
        quantities: dict[str, int] = {}
        for product in PRODUCTS:
            raw_value = str(form.get(f"quantity_{product.code}") or "0")
            try:
                quantity = int(raw_value)
            except ValueError:
                quantity = -1
            if quantity < 0 or quantity > product.stock:
                return _render_items(
                    templates,
                    request,
                    draft_id,
                    draft,
                    error=f"La quantité de {product.name} doit être comprise entre 0 et {product.stock}.",
                    status_code=400,
                )
            if quantity:
                quantities[product.code] = quantity
        if not quantities:
            return _render_items(
                templates,
                request,
                draft_id,
                draft,
                error="Sélectionnez au moins un article.",
                status_code=400,
            )
        delivery_mode = str(form.get("delivery_mode") or "standard")
        if delivery_mode not in {"standard", "express", "pickup"}:
            delivery_mode = "standard"
        with _LOCK:
            _DRAFTS[draft_id].update(
                {
                    "quantities": quantities,
                    "delivery_mode": delivery_mode,
                    "discount_code": str(form.get("discount_code") or "")
                    .strip()
                    .upper(),
                    "gift_wrap": form.get("gift_wrap") == "yes",
                }
            )
        return RedirectResponse(
            f"/demo/commandes/recapitulatif/{draft_id}", status_code=303
        )

    @router.get("/recapitulatif/{draft_id}", response_class=HTMLResponse)
    def review_page(request: Request, draft_id: str) -> Response:
        draft = _draft(draft_id)
        if draft is None or not draft.get("quantities"):
            return RedirectResponse("/demo/commandes/client", status_code=303)
        return _render_review(templates, request, draft_id, draft)

    @router.post("/recapitulatif/{draft_id}")
    def confirm_order(
        request: Request,
        draft_id: str,
        payment_method: str = Form(),
        terms: str = Form(""),
    ) -> Response:
        draft = _draft(draft_id)
        if draft is None or not draft.get("quantities"):
            return RedirectResponse("/demo/commandes/client", status_code=303)
        if terms != "accepted":
            return _render_review(
                templates,
                request,
                draft_id,
                draft,
                error="La validation des conditions est obligatoire.",
                status_code=400,
            )
        if payment_method not in {"invoice", "card", "transfer"}:
            return _render_review(
                templates,
                request,
                draft_id,
                draft,
                error="Le mode de paiement est inconnu.",
                status_code=400,
            )
        calculation = _calculate(draft)
        order_id = f"CMD-{uuid4().hex[:8].upper()}"
        status = (
            "À valider par un responsable"
            if Decimal(calculation["total_raw"]) >= Decimal("500")
            else "Confirmée"
        )
        order = {
            **draft,
            **calculation,
            "order_id": order_id,
            "payment_method": payment_method,
            "status": status,
        }
        with _LOCK:
            _ORDERS[order_id] = order
            _DRAFTS.pop(draft_id, None)
        return RedirectResponse(f"/demo/commandes/suivi/{order_id}", status_code=303)

    @router.get("/suivi/{order_id}", response_class=HTMLResponse)
    def tracking_page(request: Request, order_id: str) -> Response:
        with _LOCK:
            order = dict(_ORDERS.get(order_id, {}))
        if not order:
            return RedirectResponse("/demo/commandes/liste", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="orders_demo_tracking.html",
            context={"step": 4, "order": order, "parser_preview": False},
        )

    @router.get("/liste", response_class=HTMLResponse)
    def order_list(request: Request) -> HTMLResponse:
        with _LOCK:
            orders = tuple(reversed(tuple(_ORDERS.values())))
        return templates.TemplateResponse(
            request=request,
            name="orders_demo_list.html",
            context={"step": 4, "orders": orders},
        )

    @router.get("/parser/articles", response_class=HTMLResponse)
    def parser_items(request: Request) -> HTMLResponse:
        return _render_items(
            templates, request, "PREVIEW", _sample_draft(), parser_preview=True
        )

    @router.get("/parser/recapitulatif", response_class=HTMLResponse)
    def parser_review(request: Request) -> HTMLResponse:
        return _render_review(
            templates, request, "PREVIEW", _sample_draft(), parser_preview=True
        )

    @router.get("/parser/suivi", response_class=HTMLResponse)
    def parser_tracking(request: Request) -> HTMLResponse:
        draft = _sample_draft()
        order = {
            **draft,
            **_calculate(draft),
            "order_id": "CMD-PREVIEW",
            "payment_method": "invoice",
            "status": "Confirmée",
        }
        return templates.TemplateResponse(
            request=request,
            name="orders_demo_tracking.html",
            context={"step": 4, "order": order, "parser_preview": True},
        )

    return router


def reset_orders_demo() -> None:
    with _LOCK:
        _DRAFTS.clear()
        _ORDERS.clear()


def _draft(draft_id: str) -> dict[str, Any] | None:
    with _LOCK:
        value = _DRAFTS.get(draft_id)
        return dict(value) if value else None


def _render_client(
    templates: Jinja2Templates,
    request: Request,
    *,
    values: dict[str, Any] | None = None,
    error: str = "",
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="orders_demo_client.html",
        context={"step": 1, "values": values or {}, "error": error},
        status_code=status_code,
    )


def _render_items(
    templates: Jinja2Templates,
    request: Request,
    draft_id: str,
    draft: dict[str, Any],
    *,
    error: str = "",
    status_code: int = 200,
    parser_preview: bool = False,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="orders_demo_items.html",
        context={
            "step": 2,
            "draft_id": draft_id,
            "draft": draft,
            "products": PRODUCTS,
            "error": error,
            "parser_preview": parser_preview,
        },
        status_code=status_code,
    )


def _render_review(
    templates: Jinja2Templates,
    request: Request,
    draft_id: str,
    draft: dict[str, Any],
    *,
    error: str = "",
    status_code: int = 200,
    parser_preview: bool = False,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="orders_demo_review.html",
        context={
            "step": 3,
            "draft_id": draft_id,
            "draft": draft,
            "calculation": _calculate(draft),
            "error": error,
            "parser_preview": parser_preview,
        },
        status_code=status_code,
    )


def _calculate(draft: dict[str, Any]) -> dict[str, Any]:
    quantities = draft.get("quantities") or {}
    lines: list[dict[str, Any]] = []
    subtotal = Decimal("0")
    for product in PRODUCTS:
        quantity = int(quantities.get(product.code, 0))
        if not quantity:
            continue
        line_total = product.price * quantity
        subtotal += line_total
        lines.append(
            {
                "code": product.code,
                "name": product.name,
                "quantity": quantity,
                "unit_price": _money(product.price),
                "line_total": _money(line_total),
            }
        )
    discount = (
        (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if draft.get("discount_code") == "DEMO10"
        else Decimal("0")
    )
    shipping = {
        "standard": Decimal("6.90"),
        "express": Decimal("14.90"),
        "pickup": Decimal("0"),
    }.get(str(draft.get("delivery_mode")), Decimal("6.90"))
    if draft.get("gift_wrap"):
        shipping += Decimal("3.50")
    taxable = subtotal - discount + shipping
    tax = (taxable * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = taxable + tax
    return {
        "lines": lines,
        "subtotal": _money(subtotal),
        "discount": _money(discount),
        "shipping": _money(shipping),
        "tax": _money(tax),
        "total": _money(total),
        "total_raw": str(total),
    }


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f} €"


def _sample_draft() -> dict[str, Any]:
    return {
        "customer_name": "Ada Martin",
        "email": "ada.martin@example.test",
        "customer_type": "Entreprise",
        "requested_date": "2026-11-15",
        "priority": "Haute",
        "notes": "Livrer à l’accueil.",
        "quantities": {"CLAV-01": 2, "SUP-USB": 1},
        "delivery_mode": "standard",
        "discount_code": "DEMO10",
        "gift_wrap": True,
    }
