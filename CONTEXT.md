# Domain Glossary

## Genetic Project

User-facing label for the `Genrequest` model (`src/genlab_bestilling/models.py:232`).

Code, routes, and class names use `genrequest` (matching the model name); only
UI-facing copy (page headings, navigation labels) uses "Genetic Project(s)".

## Staff genrequest page

Unrestricted, staff-only view of a Genetic Project (`Genrequest`), gated solely
by `StaffMixin` (`src/staff/views.py`, `is_superuser` or `user.is_genlab_staff()`).

This is distinct from the customer-facing `genrequest-detail` view
(`src/genlab_bestilling/views.py`), which is scoped by
`filter_allowed(user)` ownership/organization membership. The staff page shows
every Genetic Project regardless of who owns it or which organization it
belongs to - this is what fixes the bug where staff got a page-not-found
error on genetic projects they didn't personally own.
