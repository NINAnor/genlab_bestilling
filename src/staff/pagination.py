"""Keyset ("cursor") pagination helpers for django-tables2 based staff views.

Unlike offset/page-number pagination, keyset ("seek") pagination fetches the
next batch of rows by filtering for rows that come strictly *after* the last
row of the previous page (based on the values of the fields the queryset is
ordered by), instead of using `LIMIT`/`OFFSET`. This keeps queries fast even
for tables with a huge number of rows, and - unlike offset pagination - never
skips or repeats rows when data is inserted/updated between page loads.

The cursor itself is an opaque, base64-encoded JSON list of the ordering
field values of the last row of the current page. It should only ever be
produced by `paginate_queryset` and consumed by it on a later request -
callers should treat it as an opaque token.

Known limitation: correctness of the "seek" comparison relies on the
ordering fields being non-nullable. A unique tiebreaker field is always
appended automatically (`id` by default, but configurable), so pagination
is always stable, but if a *nullable* field is used as a primary sort
column, rows with `NULL` values may not seek correctly at the null/non-null
boundary. The default ordering used by the extraction samples page avoids
this by always including a non-nullable tiebreaker.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model, Q, QuerySet
from django_tables2.utils import OrderByTuple


def _split_field(field: str) -> tuple[str, bool]:
    """Return `(field_name, descending)` for a Django `order_by()` entry."""
    if field.startswith("-"):
        return field[1:], True
    return field, False


def _column_name(model: type[Model], field_name: str) -> str:
    """Return the concrete attribute/column name to compare/read.

    For relation fields (e.g. `ForeignKey`) this returns the `*_id`
    attribute, so comparisons operate on the raw column instead of needing
    to resolve a related model instance. Non-model fields (e.g. annotated
    values added via `.annotate()`) are returned unchanged.
    """
    try:
        return model._meta.get_field(field_name).attname
    except FieldDoesNotExist:
        return field_name


def encode_cursor(ordering_fields: list[str], values: list[Any]) -> str:
    payload = json.dumps({"o": ordering_fields, "v": values}, default=str)
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str, ordering_fields: list[str]) -> list[Any] | None:
    """Decode `cursor`, returning `None` if it doesn't match `ordering_fields`.

    A cursor only makes sense for the ordering it was generated for (e.g. a
    link that changes the sort column shouldn't try to "seek" using a cursor
    produced for a different ordering) - rather than erroring out in that
    case, treat it as if no cursor was given (i.e. start from the first
    page).
    """
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        if payload.get("o") != ordering_fields:
            return None
        values = payload["v"]
    except (ValueError, KeyError, TypeError):
        return None
    else:
        return values


@dataclass
class CursorPage:
    object_list: list[Any]
    next_cursor: str | None


def ordering_fields_for(queryset: QuerySet, tiebreaker: str = "id") -> list[str]:
    """Return the ordering fields to use for `queryset`, with a tiebreaker.

    Ensures a unique field (`tiebreaker`, `id` by default) is always part of
    the ordering so that keyset pagination never skips or repeats rows.
    """
    fields = list(queryset.query.order_by)
    bare_tiebreaker = tiebreaker[1:] if tiebreaker.startswith("-") else tiebreaker
    # "id" and "pk" both refer to the primary key column.
    equivalents = {"id", "pk"} if bare_tiebreaker in ("id", "pk") else {bare_tiebreaker}
    if not any((f[1:] if f.startswith("-") else f) in equivalents for f in fields):
        fields.append(tiebreaker)
    return fields


def _seek_filter(
    model: type[Model], ordering_fields: list[str], values: list[Any]
) -> Q:
    """Build the keyset "seek" filter selecting rows strictly after `values`.

    For ordering fields `(f1, ..., fn)` and cursor values `(v1, ..., vn)` the
    condition is::

        (f1 op v1)
        OR (f1 == v1 AND f2 op v2)
        OR ...
        OR (f1 == v1 AND ... AND fn-1 == vn-1 AND fn op vn)

    where `op` is `>` for ascending fields and `<` for descending ones.
    """
    condition = Q()
    equalities: dict[str, Any] = {}
    for field, value in zip(ordering_fields, values, strict=True):
        name, descending = _split_field(field)
        column = _column_name(model, name)
        lookup = f"{column}__lt" if descending else f"{column}__gt"
        step = Q(**{lookup: value})
        if equalities:
            step &= Q(**equalities)
        condition |= step
        equalities[column] = value
    return condition


def _row_values(
    instance: Any, model: type[Model], ordering_fields: list[str]
) -> list[Any]:
    values = []
    for field in ordering_fields:
        name, _descending = _split_field(field)
        column = _column_name(model, name)
        values.append(getattr(instance, column))
    return values


def paginate_queryset(
    queryset: QuerySet,
    page_size: int,
    cursor: str | None = None,
    tiebreaker: str = "id",
) -> CursorPage:
    """Paginate `queryset` using the keyset ("seek") method.

    `queryset` should already be ordered as desired (e.g. via `.order_by()`);
    a unique `tiebreaker` field is added automatically if not already
    present, to guarantee stable pagination regardless of the primary sort.
    """
    model = queryset.model
    ordering_fields = ordering_fields_for(queryset, tiebreaker=tiebreaker)
    if ordering_fields != list(queryset.query.order_by):
        queryset = queryset.order_by(*ordering_fields)

    if cursor:
        values = decode_cursor(cursor, ordering_fields)
        if values is not None:
            queryset = queryset.filter(_seek_filter(model, ordering_fields, values))

    rows = list(queryset[: page_size + 1])
    has_next = len(rows) > page_size
    rows = rows[:page_size]

    next_cursor = None
    if has_next and rows:
        next_cursor = encode_cursor(
            ordering_fields, _row_values(rows[-1], model, ordering_fields)
        )

    return CursorPage(object_list=rows, next_cursor=next_cursor)


class CursorPaginatedTableMixin:
    """Adds cursor (keyset) pagination to a `SingleTableMixin`-based view.

    Unlike django-tables2's built-in page-number pagination, rows are
    fetched in batches of `page_size` via `paginate_queryset` above, and the
    table is rendered with a htmx "load more" trigger (see
    `staff/tables/cursor_table.html`/`_cursor_rows.html`) that fetches the
    next batch as the user scrolls, instead of numbered pages.

    Subclasses (which must also inherit `django_tables2.views.SingleTableMixin`,
    typically via `django_filters.views.FilterView`) should set:

    - `order_field_map`: maps a `sort` GET-param alias (matching a table
      column) to a tuple of the actual queryset field(s) to order/seek by
      (e.g. `{"name": ("name_as_int", "name")}` for a derived/annotated
      sort). Only columns listed here can be sorted on - this both mirrors
      which columns are orderable on the table and keeps the "seek" filter
      safe/predictable (see the module docstring above).
    - `default_order_by`: fallback tuple of aliases (from `order_field_map`)
      used when no `sort` GET param is given, e.g. `("species", "id")`.
    - `tiebreaker_field` (default `"id"`): a unique, non-nullable field
      guaranteeing stable pagination. Override this for models whose primary
      key isn't `id` (e.g. `Project.number`).
    - `page_size` (default `50`).

    The view's `get_queryset()` should *not* call `.order_by()` itself -
    ordering is fully derived from `order_field_map`/`default_order_by` (and
    the current `sort` GET param) by this mixin.
    """

    table_pagination = False
    page_size = 50
    cursor_param = "cursor"
    tiebreaker_field = "id"
    order_field_map: dict[str, tuple[str, ...]] = {}
    default_order_by: tuple[str, ...] = ()

    def _resolve_ordering(self) -> tuple[list[str], list[str]]:
        """Resolve the current sort into (queryset fields, table aliases).

        Reads the `sort` GET param (same param django-tables2 itself reads
        for header-click sorting) and maps each recognized column onto its
        underlying queryset field(s) via `order_field_map`, always appending
        `tiebreaker_field` as a unique tiebreaker for stable keyset
        pagination.
        """
        requested = self.request.GET.getlist("sort")
        aliases = [
            a
            for a in requested
            if (a[1:] if a.startswith("-") else a) in self.order_field_map
        ] or list(self.default_order_by)

        query_fields: list[str] = []
        for alias in aliases:
            name = alias[1:] if alias.startswith("-") else alias
            descending = alias.startswith("-")
            query_fields.extend(
                f"-{field}" if descending else field
                for field in self.order_field_map[name]
            )

        if self.tiebreaker_field not in query_fields and (
            f"-{self.tiebreaker_field}" not in query_fields
        ):
            query_fields.append(self.tiebreaker_field)

        return query_fields, aliases

    def get_table(self, **kwargs) -> Any:
        table_class = self.get_table_class()
        query_fields, table_order_by = self._resolve_ordering()
        queryset = self.get_table_data().order_by(*query_fields)

        cursor = self.request.GET.get(self.cursor_param)
        page = paginate_queryset(
            queryset,
            page_size=self.page_size,
            cursor=cursor,
            tiebreaker=self.tiebreaker_field,
        )

        table = table_class(data=page.object_list, **kwargs)
        table.request = self.request
        # `{% render_table %}` renders with an isolated context containing
        # only `table`, so expose `next_cursor` as an attribute on it
        # instead of (only) in the view context.
        table.next_cursor = page.next_cursor
        # Set the resolved sort directly (bypassing `Table.order_by`'s
        # setter) so the header sort arrows/links reflect the current sort
        # without triggering a redundant/incorrect in-memory re-sort of the
        # already-ordered page of rows.
        table._order_by = OrderByTuple(table_order_by)
        return table

    def get_template_names(self) -> list[str]:
        if getattr(self.request, "htmx", False):
            return ["staff/tables/_cursor_rows.html"]
        return super().get_template_names()
