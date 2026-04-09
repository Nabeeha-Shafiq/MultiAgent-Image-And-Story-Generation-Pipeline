# Test Case Scenarios
## PROJECT MONTAGE – Phase 1: The Writer's Room
### CS-4015 Agentic AI

> Run these AFTER implementation is complete. Each test case has a clear pass/fail condition.

---

## TEST GROUP 1: MCP Tool Discovery (15 rubric marks)

### TC-MCP-01: Tool Registry Returns All Required Tools
**What to do**: Start the MCP server and call the `/list_tools` endpoint (or equivalent).
**Expected output**:
```json
{
  "tools": [
    "generate_script_segment",
    "commit_memory",
    "query_stock_footage",
    "generate_character_image"
  ]
}
```
**Pass condition**: All 4 tools present in response.
**Fail condition**: Any tool missing, or tools list is hardcoded inside an agent file.

---

### TC-MCP-02: Agent Cannot Call Backend Directly
**What to do**: Search the codebase for direct imports.
```bash
grep -r "pollinations.ai" agents/
grep -r "import implementations" agents/
grep -r "requests.get" agents/
```
**Pass condition**: Zero results in `agents/` directory.
**Fail condition**: Any direct API call found inside agent files.

---

### TC-MCP-03: MCP Dispatcher Handles Unknown Tool Gracefully
**What to do**: Call the MCP dispatcher with a nonexistent tool name:
```python
dispatcher.call({"tool": "nonexistent_tool", "input": {}})
```
**Expected output**: Returns an error dict like `{"error": "Tool not found: nonexistent_tool"}` — does NOT raise an unhandled exception.
**Pass condition**: Graceful error dict returned.
**Fail condition**: Unhandled exception / stack trace crashes the pipeline.

---

## TEST GROUP 2: Script Generation — Auto Mode (15 rubric marks)

### TC-SCRIPT-01: Basic Auto-Mode Generation
**What to do**: Run `main.py` with a simple prompt. Edit the `TEST_PROMPT` variable in `main.py`:
```python
TEST_PROMPT = "A spy thriller where Agent X must stop a bioweapon from being deployed in a crowded market."
```
**Expected output**: `outputs/scene_manifest.json` created with at minimum 3 scenes.
**Pass condition**:
- File exists at `outputs/scene_manifest.json`
- Has `scenes` array with ≥ 3 entries
- Each scene has `scene_id`, `location`, `characters`, `dialogue`
- Each dialogue entry has `speaker`, `line`, `visual_cue`

**Fail condition**: File missing, malformed JSON, or missing required fields.

---

### TC-SCRIPT-02: Scene Count Matches Expectation
**What to do**: Same as TC-SCRIPT-01. Count scenes in output.
```python
import json
with open("outputs/scene_manifest.json") as f:
    data = json.load(f)
print(f"Scene count: {len(data['scenes'])}")
```
**Pass condition**: Between 3 and 10 scenes (reasonable for a single prompt).
**Fail condition**: 0 or 1 scene (generation failed silently), or 50+ scenes (hallucination spiral).

---

### TC-SCRIPT-03: Character Consistency Across Scenes
**What to do**: From the generated `scene_manifest.json`, check that character names are consistent (same spelling, same case) across all scenes.
```python
names_per_scene = [set(scene["characters"]) for scene in data["scenes"]]
all_names = set().union(*names_per_scene)
print(f"Unique character names across all scenes: {all_names}")
# Manually check: no "AgentX" and "Agent X" both appearing — they are the same character
```
**Pass condition**: Character names are consistent — no duplicates with different casing/spacing.
**Fail condition**: Same character referenced with different names ("John", "jon", "JOHN") in different scenes.

---

### TC-SCRIPT-04: Visual Cues Are Meaningful
**What to do**: Open `scene_manifest.json` and read all `visual_cue` fields.
**Pass condition**: Each visual cue is a descriptive string (e.g., "Close-up, tense lighting, sweat on character's brow") — NOT empty, NOT "N/A", NOT "visual cue".
**Fail condition**: Empty strings, placeholder text, or identical cue repeated in every scene.

---

## TEST GROUP 3: Manual Mode / Validator (Script Intake)

### TC-VAL-01: Valid Manual Script Accepted
**What to do**: Set `input_mode = "manual"` in `main.py` and provide a properly formatted script JSON (matching the spec schema).
**Expected**: Validator agent accepts it, pipeline continues to character extraction.
**Pass condition**: No validation errors, `status` in state transitions from `"validating"` to `"validated"`.

---

### TC-VAL-02: Invalid Manual Script Rejected
**What to do**: Provide a malformed script (missing `scene_id`, or `dialogue` with no `speaker` field).
```json
{
  "scenes": [
    {
      "location": "Rooftop",
      "dialogue": [{"line": "Run!"}]
    }
  ]
}
```
**Pass condition**: Validator rejects script with a clear error message listing what's missing. Pipeline does NOT crash — it either prompts for correction or exits cleanly.
**Fail condition**: Pipeline crashes with unhandled exception, or invalid script passes validation.

---

## TEST GROUP 4: LangGraph State Transitions (10 rubric marks)

### TC-GRAPH-01: Mode Selector Routes Correctly to Auto Path
**What to do**: Set `raw_input` to a plain English prompt (no JSON). Run pipeline with debug logging on.
**Expected**: Logs show transition: `mode_selector_node → scriptwriter_node`.
**Pass condition**: `scriptwriter_node` runs (not `validator_node`).

---

### TC-GRAPH-02: Mode Selector Routes Correctly to Manual Path
**What to do**: Set `raw_input` to a valid JSON script string.
**Expected**: Logs show transition: `mode_selector_node → validator_node`.
**Pass condition**: `validator_node` runs (not `scriptwriter_node`).

---

### TC-GRAPH-03: State Fields Populated at Each Node
**What to do**: Add print/log of full state after each node. Run pipeline.
**After `scriptwriter_node`**: `state["script"]` must be a non-empty dict.
**After `character_node`**: `state["characters"]` must be a non-empty list.
**After `image_node`**: `state["images"]` must be a non-empty list.
**After `memory_commit_node`**: `state["status"]` must equal `"complete"`.
**Fail condition**: Any field is still empty/None after the node responsible for it has run.

---

### TC-GRAPH-04: Reject at HITL Loops Back to Scriptwriter
**What to do**: At the HITL checkpoint, enter "REJECT".
**Expected**: Pipeline re-runs `scriptwriter_node` with same input (or amended prompt).
**Pass condition**: A second script is generated and HITL is presented again.
**Fail condition**: Pipeline exits, or HITL accepts the rejection but does nothing (dead end).

---

## TEST GROUP 5: Human-in-the-Loop (10 rubric marks)

### TC-HITL-01: Pipeline Pauses at HITL
**What to do**: Run pipeline. Observe if it pauses and waits for user input before proceeding to character/image generation.
**Pass condition**: Pipeline visibly pauses. Prompt displayed clearly (e.g., "Review the generated script. Type APPROVE to continue or REJECT to regenerate:"). Output not yet written to disk.
**Fail condition**: Pipeline runs end-to-end without any pause, or HITL is called after images are already generated.

---

### TC-HITL-02: APPROVE Continues Pipeline
**What to do**: At HITL checkpoint, type "APPROVE" (or "approve" — case insensitive).
**Pass condition**: Pipeline proceeds to `character_node`, then `image_node`.
**Fail condition**: Pipeline stops after HITL or throws error.

---

### TC-HITL-03: Invalid HITL Input Handled
**What to do**: At HITL checkpoint, type something random like "yes" or "ok" or just press Enter.
**Pass condition**: HITL re-prompts the user — it does not accept invalid input and does not crash.
**Fail condition**: Crashes, or treats any non-empty input as APPROVE.

---

## TEST GROUP 6: Output Completeness (5 rubric marks)

### TC-OUT-01: All Three Required Outputs Exist
**What to do**: After a successful full run, check:
```bash
ls outputs/scene_manifest.json
ls outputs/character_db.json
ls outputs/image_assets/
```
**Pass condition**: All three exist. `image_assets/` contains at least one `.png` file.
**Fail condition**: Any output missing.

---

### TC-OUT-02: character_db.json Schema Correct
**What to do**:
```python
import json
with open("outputs/character_db.json") as f:
    db = json.load(f)
for char in db["characters"]:
    assert "name" in char
    assert "traits" in char
    assert "appearance" in char
    assert "image_path" in char
    print(f"Character OK: {char['name']}")
```
**Pass condition**: All assertions pass for all characters.
**Fail condition**: Missing fields, or `characters` key absent entirely.

---

### TC-OUT-03: Image Files Referenced in character_db Exist on Disk
**What to do**:
```python
import os
for char in db["characters"]:
    path = char["image_path"]
    assert os.path.exists(path), f"Image missing: {path}"
    print(f"Image verified: {path}")
```
**Pass condition**: Every image path in `character_db.json` corresponds to an actual file.
**Fail condition**: Image path exists in JSON but file is missing on disk (broke link).

---

## TEST GROUP 7: Memory System (ChromaDB)

### TC-MEM-01: ChromaDB Persists Between Runs
**What to do**: Run the pipeline once. Stop it. Run it again with a different prompt.
**Pass condition**: Second run's `character_node` can query memory from the first run. Log shows "Found X existing character records in memory."
**Fail condition**: Memory is empty on second run (not persisting to disk).

---

### TC-MEM-02: Commit Memory Tool Works via MCP
**What to do**: Check logs after `memory_commit_node` runs.
**Pass condition**: Log shows MCP call to `commit_memory` tool with scene and character data. Data retrievable from ChromaDB afterward.
**Fail condition**: Memory commit called directly (not through MCP), or ChromaDB collection empty after run.

---

## TEST GROUP 8: Failure / Edge Cases

### TC-EDGE-01: Empty Prompt Handled
**What to do**: Set `TEST_PROMPT = ""` in `main.py`.
**Pass condition**: Clear error message printed. Pipeline exits cleanly without generating garbage output files.
**Fail condition**: Crashes, or generates empty/malformed `scene_manifest.json`.

---

### TC-EDGE-02: Image Generation Failure Fallback
**What to do**: Disconnect internet (or set `IMAGE_MODE = "mock"`). Run pipeline.
**Pass condition**: Pipeline continues. A placeholder/mock image is saved instead. `character_db.json` is still written.
**Fail condition**: Pipeline crashes because image generation failed.

---

### TC-EDGE-03: LLM Returns Malformed JSON for Script
**What to do**: This is harder to force manually. Instead, inspect `scriptwriter.py` for retry logic.
**Pass condition**: Code has explicit JSON validation of LLM output. If invalid JSON returned, it retries with a corrected prompt (up to `MAX_RETRIES`).
**Fail condition**: No retry logic — pipeline crashes on first bad LLM response.

---

## How to Run All Tests

After implementation, run tests in this order:

```
1. TC-MCP-01 → TC-MCP-03     (Verify MCP layer first — everything depends on it)
2. TC-GRAPH-01 → TC-GRAPH-02  (Verify routing before running full pipeline)
3. TC-VAL-01 → TC-VAL-02     (Test manual mode)
4. TC-SCRIPT-01 → TC-SCRIPT-04 (Test auto mode)
5. TC-HITL-01 → TC-HITL-03   (Test checkpoint)
6. TC-OUT-01 → TC-OUT-03     (Verify final outputs)
7. TC-MEM-01 → TC-MEM-02     (Verify persistence)
8. TC-EDGE-01 → TC-EDGE-03   (Edge cases last)
```

A full pipeline run that passes TC-SCRIPT-01, TC-HITL-01, TC-HITL-02, TC-OUT-01, TC-OUT-02, TC-OUT-03 is the minimum viable demo for grading.

---