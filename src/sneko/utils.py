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

OZ_CONFIG = """
dependencies:
 - name: OpenZeppelin
   github: OpenZeppelin/openzeppelin-contracts
   version: 5.0.2

solidity:
 import_remapping:
  - "@openzeppelin=OpenZeppelin/5.0.2"
"""

README_CONTENT = """# sneko-ape-project

So, you've generated an Ape project using sneko...

## Getting set up

- Install ape: `pip install eth-ape` (or `pipx install eth-ape` if you prefer a global install)
- Install project plugins: `ape plugins install .`
- Sanity check: `ape compile`

## Using Ape

- Run tests: `ape test`
- Deploy script: `ape run deploy`
"""

CONFTEST_CONTENT = """import pytest

@pytest.fixture
def acct1(accounts):
    return accounts[0]


@pytest.fixture
def acct2(accounts):
    return accounts[1]


@pytest.fixture
def acct3(accounts):
    return accounts[2]


# @pytest.fixture
# def example_contract(acct1, project):
#    return acct1.deploy(project.YourContract, acct1.address)
"""

SMOKE_TEST_CONTENT = """import pytest
from ape import convert


def test_smoke(acct1, acct2, acct3, example_contract):
    assert acct1.balance > 0
    assert acct2.balance > 0
    assert acct3.balance > 0

    # contract read:
    # assert example_contract.exampleFunction() == 42

    # contract write:
    # arbitrary_amount = convert("0.0001 ETH", int)
    # example_contract.doSomething("something", sender=acct1, value=arbitrary_amount)
    # assert example_contract.state_value == "something"
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
    readme_path.write_text(README_CONTENT, encoding="utf8")

    conftest_path = project_folder / "tests" / "conftest.py"
    conftest_path.touch()
    conftest_path.write_text(CONFTEST_CONTENT, encoding="utf8")

    smoke_test_path = project_folder / "tests" / "test_example_contract.py"
    smoke_test_path.touch()
    smoke_test_path.write_text(SMOKE_TEST_CONTENT, encoding="utf8")

    ape_config = project_folder / CONFIG_FILE_NAME
    ape_config.write_text(
        f"name: {project_name}\n\n"
        f"plugins:\n"
        f"  - name: {'solidity' if suffix == 'sol' else 'vyper'}\n\n"
        f"{OZ_CONFIG if suffix == 'sol' else ''}",
        encoding="utf8",
    )

    deploy_script = project_folder / "scripts" / "deploy.py"
    deploy_script.touch()
    deploy_script.write_text(DEPLOY_SCRIPT, encoding="utf8")

    print(f"{project_name} is written in {CONFIG_FILE_NAME}")
