from pathlib import Path

CONFIG_FILE_NAME = "ape-config.yaml"
GITIGNORE_CONTENT = """
# Ape stuff
.build/
.cache/

# Python
.env
.venv
.pytest_cache
.python-version
__pycache__
"""


def build_ape_project(file_name, code):
    suffix = file_name.split(".")[-1]
    cwd = Path.cwd()

    project_name = "sneko-ape-project"
    project_folder = cwd / project_name
    project_folder.mkdir()

    for folder_name in ("contracts", "tests", "scripts"):
        folder = project_folder / folder_name
        folder.mkdir()

    contract_path = project_folder / "contracts" / file_name
    contract_path.touch()
    contract_path.write_text(code, encoding="utf8")

    git_ignore_path = project_folder / ".gitignore"
    git_ignore_path.touch()
    git_ignore_path.write_text(GITIGNORE_CONTENT.lstrip(), encoding="utf8")

    readme_path = project_folder / "README.md"
    readme_path.touch()
    readme_path.write_text("TODO: ape instructions", encoding="utf8")

    ape_config = project_folder / CONFIG_FILE_NAME
    ape_config.write_text(
        f"name: {project_name}\n\n"
        f"plugins:\n"
        f"  - name: {'solidity' if suffix == 'sol' else 'vyper'}\n",
        encoding="utf8",
    )

    print(f"{project_name} is written in {CONFIG_FILE_NAME}")
