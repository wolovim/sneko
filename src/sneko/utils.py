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

DEPLOY_SCRIPT = """import click
from ape import accounts, project
from ape.cli import (
    ConnectedProviderCommand,
    network_option,
    select_account,
)

@click.command(cls=ConnectedProviderCommand)
@network_option()
def cli(ecosystem, network, provider):
    click.echo(f"You are connected to network '{ecosystem.name}:{network.name}' (chain ID: {provider.chain_id}).")
    account = select_account()
    # Replace your contract name and constructor args here:
    contract = project.YourContractName.deploy(your_args, sender=account)
    click.echo(f"Deployed contract to {contract.address} on {ecosystem.name}:{network.name}.")
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

    deploy_script = project_folder / "scripts" / "deploy.py"
    deploy_script.touch()
    deploy_script.write_text(DEPLOY_SCRIPT, encoding="utf8")

    print(f"{project_name} is written in {CONFIG_FILE_NAME}")
