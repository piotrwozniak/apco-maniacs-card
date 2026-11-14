"""Package the APCO Weather integration, including its dashboard card."""
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def package(output=ROOT / "output"):
    """Build a clean, single-integration repository and a manual-install ZIP."""
    output = Path(output)
    target = output / "apco-weather"
    component = target / "custom_components" / "apco_maniacs"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ROOT / "custom_components/apco_maniacs", component,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    guide = (ROOT / "docs/integration/README.md").read_text().replace(
        "../../custom_components/", "custom_components/")
    (target / "README.md").write_text(guide)
    shutil.copyfile(ROOT / "LICENSE", target / "LICENSE")
    shutil.copyfile(ROOT / 'hacs.json', target / 'hacs.json')
    archive = output / "apco-weather.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in sorted(component.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(target))
    return target, archive


if __name__ == "__main__":
    for path in package():
        print(path)
