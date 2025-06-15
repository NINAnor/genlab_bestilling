## Repository structure

### Root

- pyproject.toml, dependencies of the project
- pre-commit-config.yml, configuration for precommit
- aliases.sh, development shortcuts (aliases)
- entrypoint.sh, docker entrypoint script
- src, the directory contains all the source code
- nginx, the directory contains the proxy configurations
- docs, contains the mdbook pages
- media, placeholder directory for media files (user uploads)

### Source Code

- apps, wrapper module for `core` and `users` django apps
- apps.users, module that extends the default django auth user module
- apps.core, module that contains some shared functionalities (base templates, management commands, templatetags)
- config, module that contains all the configuration logic of the django project (`urls.py`, `settings`)
- frontend, implements the frontend (more on this later)
- genlab_bestilling, the module that holds all the business logic
- locale, translations folder
- fixtures, database seeds folder
- nina, module that implements models related to our organization management (projects)
- shared, code that is used in different modules
- static, static files
- templates, top level templates folder
- theme, folder that contains the theme (i.e. Tailwindcss implementation)
- staff, contains the code that implements the staff section

### Frontend
The frontend is implemented using `React`, the code is bundled with `vite` and is served as a static file (in production).
The code is organized as multi-page: inside `frontend/src` each folder will be bundled as a different javascript file, which will be loaded on a specific page.

This allows to "enhance" only certain pages, where and if necessary.

During the development, a container that executes `vite` starts a dev-server.
The production image instead builds the frontend modules in a docker stage and keeps the output (without the `node_modules` folder).

### Theme
The theme is implemented as a `django-tailwind` module.

### genlab_bestilling
Most of the files follow the conventions of django (admin, views, urls, apps), more on the others:

- api, contains the files related to `rest-framework`, such as `views` and `serializers`. Rest APIs are used by the frontend.
- libs, all the modules contain "isolated" code that should be easy to test and reuse in different contexts
- filters, filters of `django-filter`
- autocomplete, autocomplete of `dal2`
- tables, tables of `django-tables2`
- tasks, tasks of `procrastinate`
