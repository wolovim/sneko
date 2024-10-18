import json
import os
import pyperclip
import solcx
import subprocess
import sys
import vyper
import tree_sitter_types.parser as tst

from pathlib import Path
from rich.syntax import Syntax

from textual import log, on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import var, reactive
from textual.widgets import (
    Button,
    Collapsible,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)
from web3 import Web3, EthereumTesterProvider

from sneko.config import Config
from sneko.utils import build_ape_project

# import logging
# from textual.logging import TextualHandler
#
# logging.basicConfig(
#     level="DEBUG",
#     handlers=[
#        TextualHandler(),
#        logging.StreamHandler(),
#        logging.FileHandler("sneko.log")
#     ],
# )

BOLD = Config.BOLD
RESET = Config.RESET
SOLIDITY_VERSION = Config.SOLIDITY_VERSION
solcx.install_solc(SOLIDITY_VERSION)
solcx.set_solc_version(SOLIDITY_VERSION)


class Sneko(App):
    """A terminal GUI for Ethereum smart contracts"""

    CSS_PATH = Config.CSS_PATH
    BINDINGS = Config.BINDINGS

    show_tree = var(True)
    abi = None
    bytecode = None
    w3 = None
    contract = None
    constructor_args = reactive("(Compile contract first!)")
    contract_path = None
    solidity_loaded = False
    vyper_loaded = False

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""

        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Render the UI"""

        path = Config.DEFAULT_CONTRACTS_PATH if len(sys.argv) < 2 else sys.argv[1]

        yield Header()
        with Collapsible(
            title="Collapse Editor", collapsed=False, id="collapsible-editor"
        ):
            yield Container(
                DirectoryTree(path, id="tree-view"),
                TextArea.code_editor(text="", id="code-view", theme="vscode_dark"),
                id="editor",
            )
        with TabbedContent():
            with TabPane("Compile", id="compile-tab"):
                yield Container(
                    Horizontal(
                        Button(
                            "Compile",
                            id="compile-button",
                            variant="success",
                            disabled=True,
                        ),
                        Input(
                            placeholder="Compiler version ~",
                            id="compiler-version",
                            disabled=True,
                        ),
                        id="compile-grouping",
                    ),
                    Horizontal(
                        Button("Copy ABI", id="copy-abi-button", disabled=True),
                        Input(placeholder="ABI ~", id="abi-view", disabled=True),
                        id="input-abi",
                    ),
                    Horizontal(
                        Button(
                            "Copy Bytecode", id="copy-bytecode-button", disabled=True
                        ),
                        Input(
                            placeholder="Deployment bytecode ~",
                            id="bytecode-view",
                            disabled=True,
                        ),
                        id="input-bytecode",
                    ),
                    Horizontal(
                        Button(
                            "Generate Script",
                            id="generate-script-button",
                            variant="primary",
                            disabled=True,
                        ),
                        Button(
                            "Generate Ape Project",
                            id="generate-ape-button",
                            variant="primary",
                            disabled=True,
                        ),
                    ),
                    id="compilation-panel",
                )
            with TabPane("Playground", id="playground-tab"):
                yield Container(
                    Horizontal(
                        Button("Active account:", id="active-acct-button"),
                        Select((), id="acct-select"),
                        id="acct-select-horizontal",
                    ),
                    Static("", id="deploy-address"),
                    Static("", id="contract-balance"),
                    Horizontal(
                        Button(
                            "Deploy",
                            id="deploy-button",
                            variant="success",
                            disabled=True
                        ),
                        Input(
                            placeholder=f"{self.constructor_args}",
                            id="constructor-args",
                            disabled=True,
                        ),
                        id="deploy-horizontal",
                    ),
                    Static(id="playground-fn-body"),
                    id="playground-panel",
                )
        yield Footer()

    async def watch_constructor_args(self, constructor_args: str) -> None:
        """Called when constructor_args is modified."""

        input = self.query_one("#constructor-args", Input)
        if constructor_args is None or constructor_args == "":
            input.placeholder = "(no constructor args)"
            input.disabled = True
        else:
            input.placeholder = constructor_args
            input.disabled = False

    def load_syntax_highlighting(self, lang: str) -> None:
        code_view = self.query_one("#code-view", TextArea)
        code_view.loading = True
        if lang == "solidity":
            tst.install_parser("https://github.com/JoranHonig/tree-sitter-solidity.git", "tree-sitter-solidity")
            solidity_lang = tst.load_language('tree-sitter-solidity', "solidity")
            sol_highlight_query = (Path(__file__).parent / "solidity.scm").read_text()
            code_view.register_language(solidity_lang, sol_highlight_query)
            self.solidity_loaded = True
        else:
            tst.install_parser("https://github.com/madlabman/tree-sitter-vyper", "tree-sitter-vyper")
            vyper_lang = tst.load_language('tree-sitter-vyper', "vyper")
            vyper_highlight_query = (Path(__file__).parent / "vyper.scm").read_text()
            code_view.register_language(vyper_lang, vyper_highlight_query)
            self.vyper_loaded = True
        code_view.loading = False

    async def on_mount(self) -> None:
        self.w3 = Web3(EthereumTesterProvider())
        self.active_account = self.w3.eth.accounts[0]
        await self.update_account_balances()
        self.query_one(DirectoryTree).focus()

    async def update_account_balances(self) -> None:
        w3 = self.w3
        accounts = w3.eth.accounts
        options = [
            (f"{a} ({w3.from_wei(w3.eth.get_balance(a), 'ether')} ETH)", a)
            for a in accounts
        ]
        sel = self.query_one("#acct-select", Select)
        sel.set_options(options)
        sel.value = self.active_account

    async def handle_compile_error(self, e) -> None:
        if "vyper: command not found" in str(e):
            error_msg = f"{BOLD}A local installation of Vyper is required to compile Vyper contracts.{RESET}\n"
            error_msg += f"\n{str(e)}"
            self.notify(error_msg, severity="error", timeout=100)
        else:
            self.notify(str(e), severity="error", timeout=100)
        self.query_one("#abi-view", Input).value = "oop!"
        self.query_one("#bytecode-view", Input).value = "oop!"

        abi_button = self.query_one("#copy-abi-button", Button)
        abi_button.disabled = True
        bytecode_button = self.query_one("#copy-bytecode-button", Button)
        bytecode_button.disabled = True
        generate_script_button = self.query_one("#generate-script-button", Button)
        generate_script_button.disabled = True
        generate_ape_button = self.query_one("#generate-ape-button", Button)
        generate_ape_button.disabled = True

        await self.nuke_playground()

        self.abi = None
        self.bytecode = None

    def get_constructor_args(self, abi):
        for abi_value in json.loads(abi) if type(abi) == str else abi:
            if abi_value["type"] == "constructor":
                return ", ".join(
                    [f"{arg['type']} {arg['name']}" for arg in abi_value["inputs"]]
                )

    async def handle_compile_success(self):
        abi_value = self.abi
        bytecode_value = self.bytecode

        abi_input = self.query_one("#abi-view", Input)
        abi_input.value = abi_value
        abi_button = self.query_one("#copy-abi-button", Button)
        abi_button.disabled = False

        bytecode_input = self.query_one("#bytecode-view", Input)
        bytecode_input.value = bytecode_value
        bytecode_button = self.query_one("#copy-bytecode-button", Button)
        bytecode_button.disabled = False

        generate_script_button = self.query_one("#generate-script-button", Button)
        generate_script_button.disabled = False

        generate_ape_button = self.query_one("#generate-ape-button", Button)
        generate_ape_button.disabled = False

        deploy_button = self.query_one("#deploy-button", Button)
        deploy_button.disabled = False

        self.query_one("#constructor-args", Input).value = ""

    async def compile_contract(self) -> None:
        self.contract = None
        code_view = self.query_one("#code-view", TextArea)
        code = code_view.text

        file_extension = Path(self.sub_title).suffix

        try:
            # SOLIDITY:
            current_dir = os.path.dirname(__file__)
            file_path = os.path.join(
                current_dir, "contracts", "solidity", "OpenZeppelin", "v5.0.2"
            )
            if file_extension == ".sol":
                compiled_sol = solcx.compile_source(
                    code,
                    output_values=["abi", "bin", "bin-runtime"],
                    import_remappings=[f"@openzeppelin/contracts={file_path}"],
                )
                # Main contract has key: "<stdin>:<contract_name>"
                contract_key = next(
                    (key for key in compiled_sol if key.startswith("<stdin>:")), None
                )
                contract_interface = compiled_sol[contract_key]
                self.constructor_args = self.get_constructor_args(
                    json.dumps(contract_interface["abi"])
                )
                self.abi = json.dumps(contract_interface["abi"])
                self.bytecode = json.dumps(contract_interface["bin"])
            # VYPER:
            elif file_extension == ".vy":
                contract_path = Path(self.contract_path)
                contract = subprocess.run(
                    ["vyper", contract_path.resolve(), "-f", "abi,bytecode"],
                    capture_output=True,
                    text=True,
                )
                if contract.stderr:
                    await self.handle_compile_error(contract.stderr)
                    return
                else:
                    contract_artifacts = contract.stdout.split("\n")
                    self.constructor_args = self.get_constructor_args(
                        contract_artifacts[0]
                    )
                    self.abi = contract_artifacts[0]
                    self.bytecode = f'"{contract_artifacts[1]}"'
            # WAT?
            else:
                raise Exception("Unsupported file extension")
        except Exception as e:
            await self.handle_compile_error(e)
            return

        await self.handle_compile_success()

    def generate_script(self) -> None:
        """Generate a Python script to deploy the contract."""

        abi = self.query_one("#abi-view", Input).value
        bytecode = self.query_one("#bytecode-view", Input).value
        content = f"ABI={abi}\nBYTECODE={bytecode}\n\n"

        try:
            path = os.path.join(os.path.dirname(__file__), "snippets", "script.py")
            with open(path, "r") as src:
                content += src.read()
            with open("output.py", "w") as dest:
                dest.write(content)
            self.notify("Script generated: saved to ./output.py")
        except Exception as e:
            self.notify(f"Error generating script: {e}", severity="error")

    async def clear_deployed_contract(self) -> None:
        container = self.query_one("#playground-fn-body", Static)
        await container.remove_children()
        address_display = self.query_one("#deploy-address", Static)
        address_display.update("")

    async def nuke_playground(self) -> None:
        """Unmount deployed contract buttons and inputs."""

        await self.clear_deployed_contract()
        deploy_button = self.query_one("#deploy-button", Button)
        deploy_button.disabled = True
        constructor_args = self.query_one("#constructor-args", Input)
        constructor_args.value = ""

    def convert_string_to_typed_data(self, values, input_types):
        """Given a comma separated string of values, convert to typed data."""

        values_list = [a.strip() for a in values.split(",")]
        typed_values = values_list.copy()

        for i, arg in enumerate(values_list):
            if "int" in input_types[i]["type"]:
                typed_values[i] = int(arg)
            # TODO: handle remaining types

        return typed_values

    async def update_contract_balance(self, address: str) -> None:
        """Update the contract balance."""

        balance_wei = self.w3.eth.get_balance(address)
        balance_ether = self.w3.from_wei(balance_wei, "ether")

        self.query_one("#contract-balance", Static).update(
            f"Contract balance: {balance_ether} ETH"
        )

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.active_account = event.value

    async def deploy_contract(self) -> None:
        """Deploy the contract to the Ethereum network."""

        if not self.abi or not self.bytecode:
            await self.compile_contract()

        await self.clear_deployed_contract()

        w3 = self.w3
        bytecode = self.query_one("#bytecode-view", Input).value
        abi = self.query_one("#abi-view", Input).value
        bytecode = json.loads(bytecode)
        abi = json.loads(abi)

        try:
            contract = w3.eth.contract(abi=abi, bytecode=bytecode)

            constructor_types = None
            for abi_value in contract.abi:
                if abi_value["type"] == "constructor":
                    constructor_types = abi_value["inputs"]
            if constructor_types is None:
                self.notify("No constructor method found", severity="error")
                return
            constructor_arg_input = self.query_one("#constructor-args", Input).value

            tx_body = {"from": self.active_account}
            if constructor_arg_input == "":
                tx_hash = contract.constructor().transact(tx_body)
            else:
                typed_args = self.convert_string_to_typed_data(
                    constructor_arg_input, constructor_types
                )
                tx_hash = contract.constructor(*typed_args).transact(tx_body)
            self.notify(f"Transaction hash: {tx_hash.hex()}")
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            self.notify(f"Contract address: {tx_receipt.contractAddress}")

            address_display = self.query_one("#deploy-address", Static)
            address_display.update(f"Contract address: {tx_receipt.contractAddress}")
        except Exception as e:
            self.notify(f"Error deploying contract: {e}", severity="error")
            return

        try:
            deployed_contract = w3.eth.contract(
                address=tx_receipt.contractAddress, abi=abi
            )

            playground = self.query_one("#playground-fn-body", Static)
            fns = deployed_contract.all_functions()
            for fn in fns:
                is_tx = fn.abi["stateMutability"] in ["nonpayable", "payable"]
                is_payable = fn.abi["stateMutability"] == "payable"
                b = Button(
                    fn.fn_name,
                    id=f"fn-button-{fn.fn_name}",
                    classes="fn-button",
                    variant="warning" if is_tx else "primary",
                )
                fn_inputs = fn.abi["inputs"]
                if fn_inputs:
                    placeholder = ", ".join(
                        [f"{arg['type']} {arg['name']}" for arg in fn_inputs]
                    )
                    i = Input(
                        placeholder=f"{placeholder}",
                        id=f"fn-input-{fn.fn_name}",
                        classes="fn-input",
                    )
                    h = Horizontal(
                        b, i, id=f"fn-group-{fn.fn_name}", classes="fn-group"
                    )
                else:
                    h = Horizontal(b, id=f"fn-group-{fn.fn_name}", classes="fn-group")
                playground.mount(h)
                if is_payable:
                    playground.mount(
                        Horizontal(
                            Static("↳", classes="fn-value-label"),
                            Input(
                                placeholder="payable: value in wei",
                                id=f"fn-value-{fn.fn_name}",
                                classes="fn-value",
                            ),
                            classes="fn-value-grouping",
                        )
                    )
                self.contract = deployed_contract
            self.query_one("#constructor-args", Input).value = ""
            await self.update_contract_balance(tx_receipt.contractAddress)
            await self.update_account_balances()
        except Exception as e:
            self.notify(f"Error generating UI: {e}", severity="error")

    def get_contract_fn_abi(self, name):
        """Given a fn name, return the relevant ABI info"""

        for declaration in self.contract.abi:
            if declaration.get("name") == name:
                return declaration
        return None

    async def handle_contract_fn_button(self, button_id: str) -> None:
        """Handle a button click for a contract function."""

        button_id = button_id.replace("fn-button-", "")

        # determine if call or transact:
        fn_abi = self.get_contract_fn_abi(button_id)
        is_tx = fn_abi["stateMutability"] in ["nonpayable", "payable"]
        is_payable = fn_abi["stateMutability"] == "payable"

        try:
            input_value = self.query_one(f"#fn-input-{button_id}").value
        except:
            input_value = None

        try:
            value = self.query_one(f"#fn-value-{button_id}").value
        except:
            value = None

        if input_value:
            try:
                converted_input = self.convert_string_to_typed_data(
                    input_value, fn_abi["inputs"]
                )
                if is_tx:
                    tx_body = {
                        "value": int(value) if is_payable else 0,
                        "from": self.active_account,
                    }
                    tx_hash = self.contract.functions[button_id](
                        *converted_input
                    ).transact(tx_body)
                    self.notify(f"Tx hash: {tx_hash.hex()}")
                    await self.update_contract_balance(self.contract.address)
                    await self.update_account_balances()
                else:
                    response = self.contract.functions[button_id](
                        *converted_input
                    ).call()
                    self.notify(f"Function response: {response}")
            except Exception as e:
                self.notify(f"Error calling function: {e}", severity="error")
        else:
            try:
                if is_tx:
                    tx_body = {
                        "value": int(value) if is_payable else 0,
                        "from": self.active_account,
                    }
                    tx_hash = self.contract.functions[button_id]().transact(tx_body)
                    self.notify(f"Tx hash: {tx_hash.hex()}")
                    await self.update_contract_balance(self.contract.address)
                    await self.update_account_balances()
                else:
                    response = self.contract.functions[button_id]().call()
                    self.notify(f"Function response: {response}")
            except Exception as e:
                self.notify(f"Error calling function: {e}", severity="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when any button is clicked."""

        if event.button.id == "compile-button":
            await self.compile_contract()
        elif event.button.id == "generate-ape-button":
            code_view = self.query_one("#code-view", TextArea)
            try:
                build_ape_project(self.sub_title, code_view.text)
                self.notify("Ape project created in directory: sneko-ape-project")
            except Exception as e:
                self.notify(f"Error building Ape project: {e}", severity="error")
        elif event.button.id == "copy-abi-button":
            input = self.query_one("#abi-view", Input)
            pyperclip.copy(input.value)
            self.notify("ABI copied to clipboard")
        elif event.button.id == "copy-bytecode-button":
            input = self.query_one("#bytecode-view", Input)
            pyperclip.copy(input.value)
            self.notify("Bytecode copied to clipboard")
        elif event.button.id == "generate-script-button":
            self.generate_script()
        elif event.button.id == "active-acct-button":
            active_account = self.query_one("#acct-select", Select).value
            pyperclip.copy(active_account)
            self.notify("Active account copied to clipboard")
        elif event.button.id == "deploy-button":
            await self.deploy_contract()
        elif event.button.id.startswith("fn-button-"):
            await self.handle_contract_fn_button(event.button.id)
        else:
            log("unhandled button press event ~")

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when a file in the directory tree is clicked."""

        event.stop()
        code_view = self.query_one("#code-view", TextArea)
        self.contract_path = event.path
        try:
            syntax = Syntax.from_path(str(event.path))
            code_view.load_text(syntax.code)
        except Exception as e:
            code_view.load_text(str(e))
            self.sub_title = "ERROR"
        else:
            code_view.scroll_home(animate=False)

            file_name = Path(event.path).stem
            file_extension = Path(event.path).suffix
            self.sub_title = file_name + file_extension

            if file_extension == ".sol":
                if not self.solidity_loaded:
                    self.load_syntax_highlighting("solidity")
                code_view.language = "solidity"
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = f"solidity {SOLIDITY_VERSION}"
                code_view.read_only = False
            elif file_extension == ".vy":
                if not self.vyper_loaded:
                    self.load_syntax_highlighting("vyper")
                code_view.language = "vyper"
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = f"vyper {vyper.version.version}"
                code_view.read_only = True
            else:
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = "wat? only vyper and solidity supported"
                code_view.read_only = True

            compile_button = self.query_one("#compile-button", Button)
            compile_button.disabled = False
            self.reset_inputs()
            await self.nuke_playground()
            self.query_one(TabbedContent).active = "compile-tab"

    def reset_inputs(self) -> None:
        # Clear inputs
        abi_input = self.query_one("#abi-view", Input)
        abi_input.value = ""
        bytecode_input = self.query_one("#bytecode-view", Input)
        bytecode_input.value = ""

        # Disable buttons
        abi_button = self.query_one("#copy-abi-button", Button)
        abi_button.disabled = True
        bytecode_button = self.query_one("#copy-bytecode-button", Button)
        bytecode_button.disabled = True
        generate_script_button = self.query_one("#generate-script-button", Button)
        generate_script_button.disabled = True
        generate_ape_button = self.query_one("#generate-ape-button", Button)
        generate_ape_button.disabled = True

        self.abi = None
        self.bytecode = None

    # Bindings

    def action_toggle_files(self) -> None:
        self.show_tree = not self.show_tree

    def action_copy_to_clipboard(self) -> None:
        code_view = self.query_one("#code-view", TextArea)
        pyperclip.copy(code_view.text)
        self.notify("Code copied to clipboard")


def main():
    if len(sys.argv) == 1:
        Sneko().run()
    elif len(sys.argv) > 2:
        print("Error: too many arguments. See 'sneko --help' for usage.")
        sys.exit(1)
    elif sys.argv[1] in ["version", "-v", "--version"]:
        print(Config.__version__)
        sys.exit(0)
    elif sys.argv[1] in ["help", "-h", "--help"]:
        print(
            f"\n{BOLD}Sneko:{RESET} a terminal GUI for Ethereum smart contracts",
            f"\n\n{BOLD}[Usage]{RESET}\n sneko\n sneko [path]",
            f"\n\n{BOLD}[Options]{RESET}",
            "\n  -h, --help    Show this message and exit.",
            "\n  -v, --version Show the version and exit.",
            f"\n\n{BOLD}[Args]{RESET}",
            "\n  path          Path to a directory containing contracts",
        )
        sys.exit(0)
    else:
        Sneko().run()
