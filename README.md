# GenLab Bestilling System
A django project generated from: ninanor/django-template

Features:
- Docker
- REST APIs




## Requirements
- docker


## How to use
First, if you are lazy execute
```
source aliases.sh # or . aliases.sh
```
This will create some shortcuts to run docker commands.

### Development setup
```
docker compose --profile dev up -d --build
# or dpcli_dev up -d --build
```
This will build the docker images for local development and startup everything.
**NOTE**: the `docker-compose.yml` uses bind-mounts, so editing your local django files will trigger a server reload without needing to rebuild the whole image.
In case you want to install new libraries (via `apt-get` or `pip`) you will need to rebuild.

The development setup will by default create a administrator user (admin@nina.no) with password: admin.
At every container start it will apply new migrations.

#### Local dependencies
If you want better DX, install depencencies locally. This will enable autocompletion and inspection of 3rd party code.
Install `uv` and run `uv sync`.

#### Django commands
Django provides useful command line tools that can be executed with `manage.py`, to see a list of all the available commands run inside the django container `src/manage.py help`.
Check [Django documentation](https://docs.djangoproject.com/en/5.0/ref/django-admin/) for a list of the builtin commands.
Here are some examples of how to run them from your command line:
```
djcli_dev makemigrations # it will detect changes in your model files and will create SQL scripts to migrate tables accordingly
```
This is actually an alias for
```
docker compose --profile dev exec -it django-dev ./src/manage.py makemigrations
```

You can then review the migration script created and apply it with:
```
djcli_dev migrate
```

Other useful commands:
```
createsuperuser # creates a new administrator account
shell_plus # open an interactive python shell
showmigrations # shows a list of migrations, useful to know which ones are applyied
dumpdata # dump data from a table into a json file
loaddata # load data from a json file to a table
models2puml #
```

### Production setup
This setup will create docker images optimized for production, without devtools installed
```
docker compose --profile prod up -d --build
# or dpcli_prod up -d --build
```

## How to update
```
copier update --trust
```

This will try to check differences between your project and the template, if no conflicts are found you are done.
Check this [page](https://copier.readthedocs.io/en/stable/updating/) for more specific info about this feature.
