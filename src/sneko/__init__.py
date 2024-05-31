# def main() -> int:
#     print("Hello from sneko!")
#     return 0
import os
import json
import sys
import solcx
import pyperclip
import boa

from pathlib import Path
# from web3 import Web3, EthereumTesterProvider
from rich.syntax import Syntax

from textual import log
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import var
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Header,
    Input,
    TextArea,
    Select,
    Static,
)

SOLIDITY_VERSION = "0.8.24"
solcx.install_solc(SOLIDITY_VERSION)
solcx.set_solc_version(SOLIDITY_VERSION)

DEFAULT_CODE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Greeter {
    string greeting;

    constructor() {
        greeting = "Hello, World!";
    }

    function greet() public view returns (string memory) {
        return greeting;
    }
}"""


class Sneko(App):
    """Textual code browser app."""

    CSS_PATH = "main.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
        ("ctrl+p", "copy_to_clipboard"),
        ("ctrl+v", "paste_from_clipboard"),
    ]

    show_tree = var(True)

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""

        sneko_contracts_path = os.path.join(os.path.dirname(__file__), "contracts")
        path = sneko_contracts_path if len(sys.argv) < 2 else sys.argv[1]

        yield Header()
        yield Container(
            DirectoryTree(path, id="tree-view"),
            TextArea.code_editor(text="", id="code-view"),
        )
        yield Container(
            Horizontal(
                Button("Compile", id="compile-button", variant="primary"),
                Select.from_values(
                    [SOLIDITY_VERSION], value=SOLIDITY_VERSION, id="solidity-version"
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
                variant="success",
                disabled=True,
            ),
            Static("", id="error-view"),
            id="compilation-panel",
        )
        yield Footer()

    def action_copy_to_clipboard(self) -> None:
        code_view = self.query_one("#code-view", TextArea)
        pyperclip.copy(code_view.text)

    def handle_compilation(self) -> None:
        self.query_one("#error-view", Static).update("")
        code_view = self.query_one("#code-view", TextArea)
        code = code_view.text
        abi_value = ""
        bytecode_value = ""

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
                abi_value = json.dumps(contract_interface["abi"])
                bytecode_value = json.dumps(contract_interface["bin"])

            # VYPER:
            elif file_extension == ".vy":
                contract = boa.loads(code)
                abi_value = json.dumps(contract.abi)
                bytecode_value = str(contract.bytecode.hex())

            # WAT?
            else:
                raise Exception("Unsupported file extension")

        except Exception as e:
            self.query_one("#error-view", Static).update(str(e))
            self.query_one("#abi-view", Input).value = "oop!"
            self.query_one("#bytecode-view", Input).value = "oop!"

            abi_button = self.query_one("#copy-abi-button", Button)
            abi_button.disabled = True
            bytecode_button = self.query_one("#copy-bytecode-button", Button)
            bytecode_button.disabled = True
            generate_script_button = self.query_one("#generate-script-button", Button)
            generate_script_button.disabled = True
            return

        # UPDATE VIEWS
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

        # w3 = Web3(EthereumTesterProvider())
        # deploy = (
        #     w3.eth.contract(abi=contract_interface["abi"], bytecode=contract_interface["bin"])
        #     .constructor(42)
        #     .transact()
        # )
        # contract_address = w3.eth.get_transaction_receipt(deploy)["contractAddress"]
        # contract = w3.eth.contract(address=contract_address, abi=contract_interface["abi"])
        # self.query_one("#address-view", Static).update(contract_address)

    def generate_script(self) -> None:
        abi = self.query_one("#abi-view", Input).value
        bytecode = self.query_one("#bytecode-view", Input).value

        path = os.path.join(os.path.dirname(__file__), "snippets", "script.py")

        content = f"ABI={abi}\nBYTECODE={bytecode}\n\n"

        # Read the content from the source file
        with open(path, "r") as src:
            content += src.read()

        # Write the modified content to the destination file
        with open("output.py", "w") as dest:
            dest.write(content)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when any button is clicked."""

        if event.button.id == "compile-button":
            self.handle_compilation()
        elif event.button.id == "copy-abi-button":
            input = self.query_one("#abi-view", Input)
            pyperclip.copy(input.value)
        elif event.button.id == "copy-bytecode-button":
            input = self.query_one("#bytecode-view", Input)
            pyperclip.copy(input.value)
        elif event.button.id == "generate-script-button":
            self.generate_script()
        else:
            log("wat")

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code-view", TextArea)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception as e:
            code_view.load_text(str(e))
            self.sub_title = "ERROR"
        else:
            text_area = self.query_one(TextArea)
            text_area.load_text(syntax.code)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree


def main():
    Sneko().run()


if __name__ == "__main__":
    main()
