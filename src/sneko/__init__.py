import json
import logging
import os
import pyperclip
import solcx
import subprocess
import sys
import vyper

from pathlib import Path
from rich.syntax import Syntax

from textual import log
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
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)
from web3 import Web3, EthereumTesterProvider

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

# ANSI escape codes for bold text
BOLD = "\033[1m"
RESET = "\033[0m"

__version__ = "0.0.14a1"
SOLIDITY_VERSION = "0.8.26"
solcx.install_solc(SOLIDITY_VERSION)
solcx.set_solc_version(SOLIDITY_VERSION)


class Sneko(App):
    """A terminal GUI for Ethereum smart contracts"""

    CSS_PATH = "main.tcss"
    BINDINGS = [
        ("v", "noop", __version__),
        ("f", "toggle_files", "Toggle Files"),
        ("ctrl+p", "copy_to_clipboard", "Copy Code"),
        ("ctrl+v", "paste_from_clipboard"),
        ("q", "quit", "Quit"),
    ]

    show_tree = var(True)
    abi = None
    bytecode = None
    w3 = None
    contract = None
    constructor_args = reactive("constructor args ~")

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""

        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Render the UI"""

        sneko_contracts_path = os.path.join(os.path.dirname(__file__), "contracts")
        path = sneko_contracts_path if len(sys.argv) < 2 else sys.argv[1]

        yield Header()
        with Collapsible(title="Collapse Editor", collapsed=False, id="collapsible-editor"):
            yield Container(
                DirectoryTree(path, id="tree-view"),
                TextArea.code_editor(text="", id="code-view"),
                id="editor",
            )
        with TabbedContent():
            with TabPane("Compile", id="compile-tab"):
                yield Container(
                    Horizontal(
                        Button(
                            "Compile", id="compile-button", variant="success", disabled=True
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
                        Button("Copy Bytecode", id="copy-bytecode-button", disabled=True),
                        Input(
                            placeholder="Deployment bytecode ~",
                            id="bytecode-view",
                            disabled=True,
                        ),
                        id="input-bytecode",
                    ),
                    Button(
                        "Generate Script",
                        id="generate-script-button",
                        variant="primary",
                        disabled=True,
                    ),
                    Static("", id="error-view"),
                    id="compilation-panel",
                )
            with TabPane("Playground", id="playground-tab"):
                yield Container(
                    Static("", id="deploy-address"),
                    Horizontal(
                        Button("Deploy", id="deploy-button", variant="success"),
                        Input(placeholder=f"{self.constructor_args}", id="constructor-args"),
                        id="deploy-horizontal",
                    ),
                    Container(id="playground-fn-body"),
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

    def on_mount(self) -> None:
        self.w3 = Web3(EthereumTesterProvider())
        self.query_one(DirectoryTree).focus()

    def handle_compile_error(self, e) -> None:
        if "vyper: command not found" in str(e):
            error_msg = f"{BOLD}A local installation of Vyper is required to compile Vyper contracts.{RESET}\n"
            error_msg += f"\n{str(e)}"
            self.query_one("#error-view", Static).update(error_msg)
        else:
            self.query_one("#error-view", Static).update(str(e))
        self.query_one("#abi-view", Input).value = "oop!"
        self.query_one("#bytecode-view", Input).value = "oop!"

        abi_button = self.query_one("#copy-abi-button", Button)
        abi_button.disabled = True
        bytecode_button = self.query_one("#copy-bytecode-button", Button)
        bytecode_button.disabled = True
        generate_script_button = self.query_one("#generate-script-button", Button)
        generate_script_button.disabled = True

        self.abi = None
        self.bytecode = None

    def get_constructor_args(self, abi):
        for abi_value in json.loads(abi) if type(abi) == str else abi:
            if abi_value["type"] == "constructor":
                return ", ".join([f"{arg['type']} {arg['name']}" for arg in abi_value["inputs"]])

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

        self.query_one("#constructor-args", Input).value = ""
        await self.clear_deployed_contract()

    async def compile_contract(self) -> None:
        self.contract = None
        self.query_one("#error-view", Static).update("")
        code_view = self.query_one("#code-view", TextArea)
        code = code_view.text

        file_extension = Path(self.sub_title).suffix

        try:
            # SOLIDITY:
            if file_extension == ".sol":
                compiled_sol = solcx.compile_source(
                    code, output_values=["abi", "bin", "bin-runtime"]
                )
                # Note: assumes only one contract:
                contract_key = next(iter(compiled_sol))
                contract_interface = compiled_sol[contract_key]
                self.constructor_args = self.get_constructor_args(json.dumps(contract_interface["abi"]))
                self.abi = json.dumps(contract_interface["abi"])
                self.bytecode = json.dumps(contract_interface["bin"])
            # VYPER:
            elif file_extension == ".vy":
                contract_path = Path(self.sub_title)
                contract = subprocess.run(
                    ['vyper', contract_path.resolve(), '-f', 'abi,bytecode'],
                    capture_output=True,
                    text=True
                )
                if contract.stderr:
                    self.handle_compile_error(contract.stderr)
                    return
                else:
                    contract_artifacts = contract.stdout.split('\n')
                    self.constructor_args = self.get_constructor_args(contract_artifacts[0])
                    self.abi = contract_artifacts[0]
                    self.bytecode = f'"{contract_artifacts[1]}"'
            # WAT?
            else:
                raise Exception("Unsupported file extension")
        except Exception as e:
            self.handle_compile_error(e)
            return

        await self.handle_compile_success()

    def generate_script(self) -> None:
        """Generate a Python script to deploy the contract."""

        abi = self.query_one("#abi-view", Input).value
        bytecode = self.query_one("#bytecode-view", Input).value
        content = f'ABI={abi}\nBYTECODE={bytecode}\n\n'

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
        """Unmount deployed contract buttons and inputs."""

        container = self.query_one("#playground-fn-body", Container)
        await container.remove_children()
        address_display = self.query_one("#deploy-address", Static)
        address_display.update("")

    def convert_string_to_typed_data(self, values, input_types):
        """Given a comma separated string of values, convert to typed data."""

        values_list = [a.strip() for a in values.split(",")]
        typed_values = values_list.copy()

        for i, arg in enumerate(values_list):
            if "int" in input_types[i]["type"]:
                typed_values[i] = int(arg)
            # TODO: handle remaining types

        return typed_values
        
    async def deploy_contract(self) -> None:
        """Deploy the contract to the Ethereum network."""

        if not self.abi or not self.bytecode:
            self.notify("Compile the contract first", severity="error")
            return

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

            if constructor_arg_input == "":
                tx_hash = contract.constructor().transact()
            else:
                typed_args = self.convert_string_to_typed_data(constructor_arg_input, constructor_types)
                tx_hash = contract.constructor(*typed_args).transact()
            self.notify(f"Transaction hash: {tx_hash.hex()}")
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            self.notify(f"Contract address: {tx_receipt.contractAddress}")

            address_display = self.query_one("#deploy-address", Static)
            address_display.update(f"Contract address: {tx_receipt.contractAddress}")
        except Exception as e:
            self.notify(f"Error deploying contract: {e}", severity="error")
            return
            
        try:
            deployed_contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

            fns = deployed_contract.all_functions()
            for fn in fns:
                is_tx = fn.abi["stateMutability"] in ["nonpayable", "payable"]
                b = Button(fn.fn_name, id=f"fn-button-{fn.fn_name}", classes="fn-button", variant="warning" if is_tx else "primary")
                playground = self.query_one("#playground-fn-body", Container)
                fn_inputs = fn.abi["inputs"]
                if fn_inputs:
                    ph = ", ".join([f"{arg['type']} {arg['name']}" for arg in fn_inputs])
                    i = Input(placeholder=f"{ph}", id=f"fn-input-{fn.fn_name}", classes="fn-input")
                    h = Horizontal(b, i, id=f"fn-group-{fn.fn_name}", classes="fn-group")
                else:
                    h = Horizontal(b, id=f"fn-group-{fn.fn_name}", classes="fn-group")
                playground.mount(h)
                self.contract = deployed_contract
            self.query_one("#constructor-args", Input).value = ""
        except Exception as e:
            self.notify(f"Error generating UI: {e}", severity="error")


    def get_contract_fn_abi(self, name):
        """Given a fn name, return the relevant ABI info"""

        for declaration in self.contract.abi:
            if declaration.get("name") == name:
                return declaration
        return None
            
    # def is_tx_fn(self, name):
    #     """Given a fn name, return whether it is a tx or call fn"""
    #
    #     fn_abi = self.get_contract_fn_abi(name)
    #     return fn_abi["stateMutability"] in ["nonpayable", "payable"]

    def handle_contract_fn_button(self, button_id: str) -> None:
        """Handle a button click for a contract function."""
            
        button_id = button_id.replace("fn-button-", "")

        # is_tx = self.is_tx_fn(button_id)
        # determine if call or transact:
        fn_abi = self.get_contract_fn_abi(button_id)
        is_tx = fn_abi["stateMutability"] in ["nonpayable", "payable"]
        
        try:
            input_value = self.query_one(f"#fn-input-{button_id}").value
        except:
            input_value = None
            
        if input_value:
            try:
                converted_input = self.convert_string_to_typed_data(input_value, fn_abi["inputs"])
                if is_tx:
                    tx_hash = self.contract.functions[button_id](*converted_input).transact()
                    self.notify(f"Tx hash: {tx_hash.hex()}")
                else:
                    response = self.contract.functions[button_id](*converted_input).call()
                    self.notify(f"Function response: {response}")
            except Exception as e:
                self.notify(f"Error calling function: {e}", severity="error")
        else:
            try:
                if is_tx:
                    tx_hash = self.contract.functions[button_id]().transact()
                    self.notify(f"Tx hash: {tx_hash.hex()}")
                else:
                    response = self.contract.functions[button_id]().call()
                    self.notify(f"Function response: {response}")
            except Exception as e:
                self.notify(f"Error calling function: {e}", severity="error")
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when any button is clicked."""

        if event.button.id == "compile-button":
            await self.compile_contract()
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
        elif event.button.id == "deploy-button":
            await self.deploy_contract()
        elif event.button.id.startswith("fn-button-"):
            self.handle_contract_fn_button(event.button.id)
        else:
            log("unhandled button press event ~")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when a file in the directory tree is clicked."""

        event.stop()
        code_view = self.query_one("#code-view", TextArea)
        try:
            syntax = Syntax.from_path(str(event.path))
        except Exception as e:
            code_view.load_text(str(e))
            self.sub_title = "ERROR"
        else:
            text_area = self.query_one(TextArea)
            text_area.load_text(syntax.code)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)

            file_extension = Path(event.path).suffix
            if file_extension == ".sol":
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = f"solidity {SOLIDITY_VERSION}"
            elif file_extension == ".vy":
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = f"vyper {vyper.version.version}"
            else:
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = "wat? only vyper and solidity supported"

            compile_button = self.query_one("#compile-button", Button)
            compile_button.disabled = False
            self.reset_inputs()
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
        print(__version__)
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


if __name__ == "__main__":
    main()
