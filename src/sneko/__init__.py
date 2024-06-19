# def main() -> int:
#     print("Hello from sneko!")
#     return 0
import os
import json
import sys
import toml
import solcx
import pyperclip
import boa

from pathlib import Path
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
    Static,
)

SOLIDITY_VERSION = "0.8.26"
solcx.install_solc(SOLIDITY_VERSION)
solcx.set_solc_version(SOLIDITY_VERSION)

with open("pyproject.toml", "r") as file:
    pyproject_data = toml.load(file)
    __version__ = pyproject_data["project"]["version"]


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

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""

        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Render the UI"""

        sneko_contracts_path = os.path.join(os.path.dirname(__file__), "contracts")
        path = sneko_contracts_path if len(sys.argv) < 2 else sys.argv[1]

        yield Header()
        # TODO: collapsible code view
        yield Container(
            DirectoryTree(path, id="tree-view"),
            TextArea.code_editor(text="", id="code-view"),
            id="editor",
        )
        yield Container(
            Horizontal(
                Button(
                    "Compile", id="compile-button", variant="primary", disabled=True
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
                variant="success",
                disabled=True,
            ),
            Static("", id="deploy-address"),
            Static("", id="error-view"),
            id="compilation-panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def handle_compile_error(self, e) -> None:
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

    def handle_compile_success(self):
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

    def handle_compilation(self) -> None:
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
                self.abi = json.dumps(contract_interface["abi"])
                self.bytecode = json.dumps(contract_interface["bin"])
            # VYPER:
            elif file_extension == ".vy":
                contract = boa.loads(code)
                self.abi = json.dumps(contract.abi)
                self.bytecode = f'"{contract.compiler_data.bytecode.hex()}"'
            # WAT?
            else:
                raise Exception("Unsupported file extension")
        except Exception as e:
            self.handle_compile_error(e)
            return

        self.handle_compile_success()

    def generate_script(self) -> None:
        """Generate a Python script to deploy the contract."""

        abi = self.query_one("#abi-view", Input).value
        bytecode = self.query_one("#bytecode-view", Input).value
        code_view = self.query_one("#code-view", TextArea)
        code = code_view.text
        content = f'CODE="""{code}"""\nABI={abi}\nBYTECODE={bytecode}\n\n'

        try:
            path = os.path.join(os.path.dirname(__file__), "snippets", "script.py")
            with open(path, "r") as src:
                content += src.read()
            with open("output.py", "w") as dest:
                dest.write(content)
            self.notify("Script generated: saved to ./output.py")
        except Exception as e:
            self.notify(f"Error generating script: {e}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when any button is clicked."""

        if event.button.id == "compile-button":
            self.handle_compilation()
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
        else:
            log("wat")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when a file in the directory tree is clicked."""

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

            file_extension = Path(event.path).suffix
            if file_extension == ".sol":
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = f"solidity {SOLIDITY_VERSION}"
            elif file_extension == ".vy":
                compiler_input = self.query_one("#compiler-version", Input)
                vyper_version = boa.contracts.vyper.vyper_contract.vyper.version.version
                compiler_input.value = f"vyper {vyper_version}"
            else:
                compiler_input = self.query_one("#compiler-version", Input)
                compiler_input.value = "wat? only vyper and solidity supported"

            compile_button = self.query_one("#compile-button", Button)
            compile_button.disabled = False
            self.reset_inputs()

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
    # ANSI escape codes for bold text
    BOLD = "\033[1m"
    RESET = "\033[0m"

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
