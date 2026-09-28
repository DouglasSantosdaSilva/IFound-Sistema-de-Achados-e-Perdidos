# Copilot instructions for iFound

## Project overview
- This is a Django app for a campus lost-and-found system. The core app is `ifound/`, while `config/` contains project wiring (`settings.py`, `urls.py`).
- The app uses SQLite (`db.sqlite3`) for local development and standard Django auth + `User` model; profile data is stored in `Perfil` and items in `Item`/`Solicitacao` in `ifound/models.py`.
- Most UI is built with Django templates in `templates/`, a shared base layout in `templates/base.html`, and shared styling in `static/css/style.css`.

## Key patterns
- Routes are declared in `ifound/urls.py`; use the existing `name=` values such as `index`, `perfil`, `cadastrar_item`, and `meus_itens` when linking templates.
- Views are in `ifound/views.py`; keep business logic there and render templates with `render(request, 'template.html', {...})`.
- The project uses plain HTML + CSS + vanilla JS, not a JS framework. Reuse the existing CSS classes from `style.css` before adding new styles.
- The SUAP integration in `login_view` is a unique project requirement: login hits the external SUAP API, then creates or updates `User` and `Perfil` records without introducing a new auth layer.

## Workflow
- Run local checks with `python manage.py check` and `python manage.py migrate` when schema or model changes are needed.
- Start the app with `python manage.py runserver` from the project root.
- Static files are served from `static/` and media from `media/` via `config/settings.py`.

## Front-end conventions
- Use `{% extends 'base.html' %}` and `{% load static %}` in templates that need the shared navbar/layout.
- For static assets, use `{% static '...' %}` and avoid hard-coded paths.
- Keep page-specific styles close to the existing CSS block structure in `static/css/style.css` rather than creating a second CSS system.
- For the My Items page, keep the minimal table/list-and-badge pattern that matches the existing green/neutral palette used throughout the app.

## Data and integrations
- Some logic expects file uploads (`ImageField`) and the app is already configured to serve them from `media/` in development.
- The login flow and item creation flow are tied to authenticated users (`@login_required`), so new pages that show user-owned data should follow the same pattern.
- When a future backend is added, keep the front-end prepared to accept a list of dictionaries with `id`, `titulo`, `data`, `detalhes`, and `status` as in the current `meus_itens` example.
