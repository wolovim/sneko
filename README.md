# sneko

Terminal GUI for compiling (Solidity and Vyper) smart contracts.

<img width="760" alt="sneko-v0.1.1" src="https://github.com/user-attachments/assets/4975a2d3-b635-417d-947f-385e04a3ce85">

## install & usage

- install [pipx](https://pipx.pypa.io/latest/installation/)
- `pipx install sneko`
- `sneko` - to view default contracts
- `sneko <path>` - to display an arbitrary directory

## local development

- install [rye](https://rye.astral.sh/guide/installation/)
- clone repo, then `rye sync`
- `textual console` in one pane
- `textual run src/sneko/__init__.py --dev` in another pane
- if not using textual devtools: `rye run sneko <path>`

## motivation

`sneko` started from a desire to "dogfood" EF Python tools (e.g., [web3.py](https://github.com/ethereum/web3.py)) in order to identify pain points and opportunities for improvement. Currently viewed as an experimental prototype editor - the sort of thing that will help you get off and running more quickly at a hackathon or illustrate a concept within a workshop. The aim is to grow `sneko` to include a well-rounded baseline of contracts and inspection tools for educational and prototyping purposes - not to be a production deployment environment.
