#import sys
from pathlib import Path

#import papermill as pm
from ruamel.yaml import YAML
from pyprojroot import here

# Get project root
root_path = Path(here())

# load recipe
yaml=YAML()
with open(root_path.joinpath('recipe.yml'), 'r') as f:
    cfg = yaml.load(f)

# generate TOC
toc = {}
toc = {
    'format': 'jb-book',
    'root': cfg['diagnostics']['root'],
    'chapters': cfg['diagnostics']['chapters']
}
with open(root_path.joinpath('notebooks/_toc.yml'), 'w') as f:
    yaml.dump(toc, f)

# prepare notebooks (inject to all ipynb)
#notebooks = Path("notebooks")
#pynbs = sorted([notebooks / "index.ipynb", *notebooks.glob("*/*.ipynb")])
#pynbs = [
#    p for p in pynbs
#    if not p.name.startswith("intro")
#    and not any(part.startswith(".") for part in p.parts)
#]

#for pynb in pynbs:
#    out = pynb.relative_to(notebooks)
#    out.parent.mkdir(parents=True, exist_ok=True)
#    pm.execute_notebook(
#        str(pynb),
#        str(out),
#        parameters=cfg['experiment'],
#        prepare_only=True,
#        log_level="ERROR",
#    )

# save settings to a YAML file
settings = {}
settings = {
    "blomster": cfg["blomster"],
    "experiment": cfg["experiment"],
    "jupyterbook": cfg["jupyterbook"],
    "grids": cfg["grids"],
    "datasets": cfg["datasets"]
}

with open(root_path.joinpath('notebooks/settings.yml'), "w") as f:
    yaml.dump(settings, f)
