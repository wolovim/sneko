# sneko

Terminal GUI for compiling (Solidity and Vyper) smart contracts.

## install

- `pipx install sneko`
- `sneko` - to view default contracts
- `sneko <path>` - to display an arbitrary directory

## possible extensions

- syntax highlighting
- module support
- select compiler version
- eth-tester deploys + function & state read-outs
- additional language support, e.g., Fe, Cairo
- additional starter scripts
- more default contracts, e.g, snekmate, solady
- generate an Ape template project

## local development

- install [rye](https://rye.astral.sh/guide/installation/)
- clone repo, then `rye sync`
- `textual console` in one pane
- `textual run src/sneko/__init__.py --dev` in another pane
