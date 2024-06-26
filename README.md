# sneko

Terminal GUI for compiling (Solidity and Vyper) smart contracts.

<img width="760" alt="sneko-v0.0.5" src="https://github.com/wolovim/sneko/assets/3621728/c4e567f8-34d1-43dc-b404-94bcbaa6859a">

## install & usage

- install [pipx](https://pipx.pypa.io/latest/installation/)
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
- if not using textual devtools: `rye run sneko <path>`
