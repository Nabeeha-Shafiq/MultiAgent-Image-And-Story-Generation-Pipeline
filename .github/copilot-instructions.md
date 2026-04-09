always use venv and install any kind of dependencies into venv - MAKE SURE THE VENV/ PIP INSTALLS TAKES UP SPACE IN ROOT OF WORKSPACE IE [ /media/hp/ADATA HV300 DRIVE] - DO NOT USE SYSTEM OR ROOT SPACE FOR ANYTHING - I AM LOW ON DISK SPACE ALREADY HENCE USING EXTERNAL DRIVE

- as of langchain-google-genai 4.0.0, the package uses the consolidated google-genai SDK instead of the legacy google-ai-generativelanguage SDK LangChain, so make sure requirements.txt pins langchain-google-genai>=4.0.0 or it may install an older incompatible version.


- NEVER import from `implementations.py` directly in any agent file. All tool calls MUST go through `mcp_server.py` dispatcher using structured JSON payloads.
- NEVER hardcode API keys, URLs, or model names. All must come from `config.py` which reads from `.env`.
- ALL LangGraph nodes must be pure functions: `def node_name(state: State) -> dict`.
- ALL agent functions must contain an explicit interpret → act → observe loop with retry logic.

## Code Style Rules
- Use Python type hints everywhere (`State`, `Dict`, `List`, `Literal`).
- Every function must have a docstring describing its role in the pipeline.
- Log all state transitions using Python `logging` module (not print).
- All JSON outputs must be validated against the pinned schemas in `config.py` before writing to disk.

## LangGraph Rules
- Always use `add_conditional_edges` for branching logic — never use if/else inside a node to route.
- HITL node must use LangGraph `interrupt_before` mechanism, not raw `input()`.
- StateGraph must be compiled with `MemorySaver` checkpointer.

## Output Rules
- `scene_manifest.json` and `character_db.json` must match the exact schemas defined in the assignment spec.
- Image files must be saved as PNG in `outputs/image_assets/{character_name}.png`.
- All outputs must be written atomically (write to temp file, then rename).

## Security Rules
- `.env` must be in `.gitignore`. Never commit API keys.
- If an API call fails, log the error and then use the next model (gemini api key provided n env provides rollong on multiple gemini models) so roll between them — never crash the pipeline.

7. Priority Order for Implementation
implement in this exact order to avoid dependency hell:
config.py and .env setup
state.py (TypedDict schema)
tools/implementations.py (raw backend calls)
tools/mcp_server.py (dispatcher wrapping implementations)
memory/db.py (ChromaDB interface)
agents/scriptwriter.py
agents/validator.py
agents/character.py
agents/image_synth.py
agents/hitl.py
main.py (LangGraph assembly — do this LAST)
