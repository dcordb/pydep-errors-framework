## Pydep

A framework that tries to fix dependency errors of Python projects.

### Thesis

This framework is the result of my work on my bachelor's thesis which you can
find [here](resources/thesis.pdf) (in Spanish).

### Usage

Checkout `pydep --help` for details.

### Developing

To develop you need to setup a virtual environment for this project, using by
example the `venv` module, and then you need to install [flit](https://pypi.org/project/flit/)
in that environment to install dependencies.

Once inside the virtual environment install `flit` with `pip install flit`.
Then install all development dependencies with `make dev` which does:

```
flit install -s --deps=develop
```

Note that this installs this project in [development
mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).
