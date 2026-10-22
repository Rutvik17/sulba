A host such as Render runs the desk from an image: a file system with the desk, its Python and its packages, and the command that starts it. A `Dockerfile` says how to build one, and `docker build` follows it.

Write the desk's `Dockerfile`, in three stages:

- the page: on a Node image, the packages `package-lock.json` pins, installed with `npm ci --ignore-scripts`, and the page compiled with the project's tsc and `tsconfig.build.json` into `static/`;
- the packages: on a Python image, with uv, the packages `uv.lock` pins, installed so that the build fails if the lock is out of date, and without the `dev` group, which only the tests use;
- the desk, on the same Python image as the packages: the packages' environment, the desk's `.py` files, `data/` and the page's `static/`, run as a user that isn't root, with a `HEALTHCHECK` that asks the desk's `/health`, and `python main.py` as its `CMD`, in exec form.

The tests read the `Dockerfile`; a run doesn't build it. If you have Docker or another builder, build the image and run it with the desk's settings:

```sh
docker build --tag desk .
docker run --rm --publish 8000:8000 --env-file desk.env desk
```

`desk.env` holds the settings, one `NAME=value` a line, and stays out of every file you share.
