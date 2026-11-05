# Plan: Compare Gilded Rose Kata With vs. Without Skill Pack

## Goal

Measure whether installing the Argus skill pack (https://github.com/pmurasky/argus) changes the agent's ability to solve the
Gilded Rose kata. Run the **same goal-level prompt** twice against an identical
starting point:

1. **Run A — Baseline:** no skill pack.
2. **Run B — Skills:** with the skill pack installed.

For each run, record **wall-clock time** and **number of commits created**, then
compare the results (plus correctness/quality as secondary signals).

> Principle: the prompt states **the goal only** — not how to accomplish it. The
> agent decides the approach.

---

## The Prompt (identical for both runs)

Paste this verbatim when starting each run:

```text
Solve the Gilded Rose kata in this repository, using the Java implementation
(`Java/`).

Goal: make the inventory updater satisfy the Gilded Rose specification and pass
the project's test suite.

Specification:
- All items have a SellIn value (days left to sell) and a Quality value.
- At the end of each day, both values update.
- Normal items lose 1 Quality per day, and 2 per day once the sell-by date has passed.
- Aged Brie gains 1 Quality per day, and 2 per day once the sell-by date has passed.
- Backstage passes gain 1 Quality per day when SellIn > 10, 2 when 10 >= SellIn > 5,
  3 when 5 >= SellIn > 0, and drop to 0 after the concert.
- Sulfuras never changes its SellIn or Quality.
- Conjured items lose 2 Quality per day (4 per day once the sell-by date has passed).
- Quality is never negative and never exceeds 50.

Work in the current repository. Run the tests to verify your changes, and commit
your work when you are done.
```

Notes:
- Do **not** add hints, TDD instructions, refactoring advice, folder layout, or tool
  suggestions. Those are "how", which would contaminate the comparison.
- Use the exact same prompt text in both runs.
- The language is fixed to **Java** (`Java/`) for both runs so language choice does
  not confound the comparison.
- If the kata source is missing, the prompt/setup must still be identical across runs
  (see Preconditions).

---

## Metrics to Capture

| Metric | How to capture |
| --- | --- |
| Wall-clock time | `start=$(date +%s)` before, `end=$(date +%s)` after; record `end-start` |
| Commits created | `git rev-list --count "$START_SHA"..HEAD` |
| Tests passing | test command result at end of run |
| Skill activated | Run B only: verify a `tool_use` event with `part.tool == "skill"` (see B4) |
| Files/lines changed | `git diff --stat "$START_SHA"..HEAD` |
| Final state clean | `git status --porcelain` empty |

Optional (quality signals): number of test runs, whether tests were added, diff size,
whether the agent refactored or only patched conditions.

---

## Preconditions / Setup (do once)

Both runs start from this fork of
[GildedRose-Refactoring-Kata](https://github.com/ehei/GildedRose-Refactoring-Kata)
`main` branch. Put the repo on exactly that commit and tag it as `baseline`:

```bash
cd /home/tsudonymn/code-agent

# Point at the forked kata repo (add or update the remote)
git remote add gildedrose https://github.com/ehei/GildedRose-Refactoring-Kata.git 2>/dev/null || \
  git remote set-url gildedrose https://github.com/ehei/GildedRose-Refactoring-Kata.git

# Fetch upstream main and check it out locally as main
git fetch gildedrose main
git checkout -B main gildedrose/main

# Pin the exact forked-kata commit every run will start from
git tag -f baseline gildedrose/main

# Confirm the local main and baseline both match the fork
test "$(git rev-parse HEAD)" = "$(git rev-parse gildedrose/main)" \
  && echo "main == ehei/GildedRose-Refactoring-Kata main"

# Make sure the working tree is pristine before the first run
git status --porcelain
```

`baseline` is now the `ehei/GildedRose-Refactoring-Kata` `main` commit
(`git rev-parse baseline` == `git rev-parse gildedrose/main`). Both runs must
start from that exact commit. If local files remain in the tree, move them out or
remove them so the starting content is identical across runs.

---

## Preflight — Verify Initial State (required before Run A and Run B)

Run this **before starting either run**. Do not proceed unless every check passes.
If a skill pack is detected, **stop and ask the user to uninstall it** — do not
silently delete or auto-uninstall files.

```bash
cd /home/tsudonymn/code-agent

# 1. Must be at main and at the baseline commit from the fork's main
git checkout main
git fetch gildedrose main
test "$(git rev-parse --abbrev-ref HEAD)" = "main" \
  || { echo "FAIL: not on main"; exit 1; }
test "$(git rev-parse baseline)" = "$(git rev-parse gildedrose/main)" \
  || { echo "FAIL: baseline is not GildedRose-Refactoring-Kata main"; exit 1; }
git reset --hard baseline
test -z "$(git status --porcelain)" \
  || { echo "FAIL: working tree is dirty"; exit 1; }
test "$(git rev-parse HEAD)" = "$(git rev-parse baseline)" \
  || { echo "FAIL: HEAD is not baseline"; exit 1; }

# 2. Detect an installed skill pack (Argus generated files)
SKILL_HITS=()
[ -f .argus.yml ]                      && SKILL_HITS+=(".argus.yml")
[ -d .opencode/skills ]                && SKILL_HITS+=(".opencode/skills/")
[ -d .opencode/commands ]              && SKILL_HITS+=(".opencode/commands/")
[ -d .claude/skills ]                  && SKILL_HITS+=(".claude/skills/")
[ -d .claude/rules ]                   && SKILL_HITS+=(".claude/rules/")
[ -d .cursor/rules ]                   && SKILL_HITS+=(".cursor/rules/")
[ -f .github/copilot-instructions.md ] && SKILL_HITS+=(".github/copilot-instructions.md")
[ -f opencode.json ] && grep -qi 'argus' opencode.json \
  && SKILL_HITS+=("opencode.json (argus instructions)")
[ -f AGENTS.md ] && grep -qiE 'argus|\.opencode/skills|skill tool' AGENTS.md \
  && SKILL_HITS+=("AGENTS.md (argus/skill reference)")

if [ "${#SKILL_HITS[@]}" -gt 0 ]; then
  echo "BLOCKED: skill pack detected in the initial state:"
  printf '  - %s\n' "${SKILL_HITS[@]}"
  echo "Ask the user to uninstall it, then re-run preflight."
  exit 1
fi

# 3. Ask about the Argus CLI (installed tooling, even without generated files)
if command -v argus >/dev/null 2>&1; then
  echo "WARNING: 'argus' is installed on PATH ($(argus --version 2>/dev/null))"
  echo "Ask the user to uninstall it before the baseline run: pip uninstall argus-standards"
  exit 1
fi

echo "PASS: on main at baseline, clean tree, no skill pack installed."
```

### If the preflight blocks: uninstall and prepare the baseline

Only do this **after the user confirms**. Preflight blocks when a skill pack is
installed or the starting state is wrong. Restore the baseline as follows.

#### 1. Remove the Argus CLI and generated files

```bash
pip uninstall -y --break-system-packages argus-standards
command -v argus >/dev/null 2>&1 && echo "still installed" || echo "argus removed"

cd /home/tsudonymn/code-agent
rm -rf .argus.yml .opencode .claude .cursor .github \
       AGENTS.md CLAUDE.md opencode.json
```

Notes:

- `--break-system-packages` is required on PEP 668-managed distros when Argus was
  installed with `pip --user`; it only removes the user install.
- Delete only Argus-generated files. Keep the kata repo and `compare-skill.md`.
- Also check for a global pack (`~/.config/opencode/AGENTS.md`,
  `~/.config/opencode/skills/`) and remove it if present.

#### 2. Locate the kata repo and pin the baseline

If the kata is nested (e.g. `GildedRose-Refactoring-Kata/`), run the setup in that
directory instead of the workspace root:

```bash
cd /home/tsudonymn/code-agent/GildedRose-Refactoring-Kata

git remote add gildedrose https://github.com/ehei/GildedRose-Refactoring-Kata.git \
  2>/dev/null || \
  git remote set-url gildedrose https://github.com/ehei/GildedRose-Refactoring-Kata.git
git fetch gildedrose main
git checkout -B main gildedrose/main
git tag -f baseline gildedrose/main
git reset --hard baseline
git clean -fdx
```

`git clean -fdx` (not `-fd`) also removes ignored build outputs such as
`Java/build/`, `Java/.gradle/`, `Java/target/`, and `python/__pycache__/`, so the
starting content is identical across runs. Remove agent-created temp artifacts too:

```bash
rm -rf /tmp/jdk /tmp/hidden /tmp/GildedRose.java
```

#### 3. Ensure the Java toolchain is available (identical for both runs)

```bash
cd /home/tsudonymn/code-agent/GildedRose-Refactoring-Kata/Java
export JAVA_HOME="${JAVA_HOME:-$HOME/.local/opt/jdk-17.0.21+9}"
export PATH="$JAVA_HOME/bin:$PATH"
java -version && ./gradlew --version >/dev/null && echo "Java toolchain ready"
```

Use the same JDK for both runs. Do not count toolchain setup toward either run's
time.

#### 4. Re-run the Preflight

Confirm `PASS` before starting the clock, then continue with Run A. Record that the
preflight passed before starting the clock.

---

## Run A — Baseline (no skill pack)

Run the **Preflight** above first, then:

```bash
cd /home/tsudonymn/code-agent
START_SHA=$(git rev-parse HEAD)

start=$(date +%s)
# --- run the agent with the prompt above, in this directory ---
end=$(date +%s)
```

After the agent finishes:

```bash
echo "Run A seconds: $((end - start))"
echo "Run A commits: $(git rev-list --count "$START_SHA"..HEAD)"
git diff --stat "$START_SHA"..HEAD
git status --porcelain
```

Record results and preserve evidence:

```bash
git bundle create /tmp/run-a.bundle --all
git log --oneline "$START_SHA"..HEAD > /tmp/run-a-commits.txt
```

---

## Run B — With Skill Pack

### B1. Reset to the identical baseline and verify the pre-run state

Run the **Preflight** above. It requires the repo to be on `main` at `baseline`
with a clean tree **and** confirms no skill pack (Argus files or CLI) is present.
If it reports the skill pack is installed, **ask the user to uninstall it** and
re-run the preflight — do not continue until it passes.

```bash
cd /home/tsudonymn/code-agent
git checkout main
git reset --hard baseline
git clean -fd
```

Only after the preflight passes should you install the skill pack below.

### B2. Install the skill pack (Argus)

The skill pack is delivered by [Argus](https://github.com/pmurasky/argus), which
generates platform instruction/skill files from composable standards packs.

> **Timing note:** install time is **not** part of the run time. Install and verify
> first, commit the generated files, then start the clock for Run B.

#### B2.1 Install Argus (the tool first)

Argus requires Python 3.11+.

```bash
pip install argus-standards
```

If generated `SKILL.md` files lack `---` frontmatter, OpenCode filters them out
and the comparison will not actually run with skills. Use a build that emits
frontmatter, e.g. the fixed fork branch:

```bash
pip install "git+https://github.com/tsudonymn/argus.git@fix/opencode-skill-frontmatter-tdd"
```

#### B2.2 Install with all packages and all supported platforms

Create `.argus.yml` in the repo root containing **all** available packs:

```yaml
packs:
  - tdd
  - atomic-commit
  - solid
  - code-quality
  - pre-commit
  - error-handling
  - type-safety
  - documentation-standards
  - dependency-injection
  - design-patterns
  - refactoring
  - testing-strategy

platforms:
  - claude
  - cursor
  - copilot
  - opencode
```

Then generate the platform files. `argus generate` writes instruction/skill files
for **every supported platform it detects in this project** (e.g. OpenCode,
Claude Code, Cursor, Copilot), plus `AGENTS.md`.

```bash
argus generate
```

If a platform needed for the comparison is not auto-detected, confirm the detected
set first (see B2.3) and ensure that platform's directory/config exists before
re-running `argus generate`. For this repo the relevant platform is **OpenCode**,
which produces:

```text
opencode.json
.opencode/skills/{pack}/SKILL.md
.opencode/commands/{pack}.md
AGENTS.md
```

#### B2.3 Verify Argus is initialized and available

```bash
argus --version
argus validate
argus packs list
argus platforms list
```

Confirm the expected files exist and are non-empty:

```bash
ls -la .argus.yml opencode.json AGENTS.md
ls .opencode/skills .opencode/commands
```

`argus generate --check` should exit 0 (no drift) after generation:

```bash
argus generate --check
```

#### B2.4 Advertise the Argus skills as mandatory in AGENTS.md

OpenCode lists loaded skills to the model, but the agent only sees the full pack
instructions after it invokes the `skill` tool. Put an explicit, mandatory pointer
in `AGENTS.md` so the agent is instructed to load the relevant packs before it
plans, edits, or runs commands.

Append a marked block (the marker must look like `name:subname` so `argus
generate` preserves it):

```bash
python3 - <<'PY'
from pathlib import Path
import yaml

packs = yaml.safe_load(Path(".argus.yml").read_text())["packs"]
block = (
    "<!-- argus:skills:start -->\n"
    "## Argus Skills (mandatory)\n\n"
    "This repository has Argus skill packs installed under `.opencode/skills/`.\n"
    "**Before planning, editing, or running any command, you MUST invoke the\n"
    "`skill` tool with the relevant pack name(s).** Do not rely on this summary\n"
    "or on `AGENTS.md` alone; the tool loads the authoritative instructions.\n\n"
    "Available packs:\n\n"
    + "\n".join(f"- `{p}`" for p in packs)
    + "\n<!-- argus:skills:end -->\n"
)

path = Path("AGENTS.md")
text = path.read_text() if path.exists() else ""
start = text.find("<!-- argus:skills:start -->")
if start == -1:
    text = text.rstrip("\n") + "\n\n" + block
else:
    end = text.find("<!-- argus:skills:end -->", start)
    end = len(text) if end == -1 else end + len("<!-- argus:skills:end -->\n")
    text = text[:start] + block + text[end:]
path.write_text(text)
PY
```

Re-run `argus generate` once so the marked block is merged into the generated file,
then confirm there is no drift and that every pack is advertised:

```bash
argus generate
argus generate --check
grep -q 'argus:skills:start' AGENTS.md

python3 - <<'PY'
from pathlib import Path
import yaml

packs = yaml.safe_load(Path(".argus.yml").read_text())["packs"]
text = Path("AGENTS.md").read_text()
missing = [p for p in packs if f"- `{p}`" not in text]
if missing:
    raise SystemExit(f"FAIL: AGENTS.md does not list: {missing}")
print(f"PASS: AGENTS.md advertises {len(packs)} Argus skills")
PY
```

#### B2.5 Verify OpenCode loaded and can run the Argus skills

Generated `SKILL.md` files are silently ignored unless they start with YAML
frontmatter containing `name` and `description`. Validate the files first:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml

skills = sorted(Path(".opencode/skills").glob("*/SKILL.md"))
bad = []
for path in skills:
    text = path.read_text()
    if not text.startswith("---\n"):
        bad.append(f"{path}: missing frontmatter")
        continue
    _, frontmatter, _ = text.split("---\n", 2)
    data = yaml.safe_load(frontmatter) or {}
    if data.get("name") != path.parent.name or not data.get("description"):
        bad.append(f"{path}: missing/incorrect name or description")
if bad:
    raise SystemExit("FAIL:\n" + "\n".join(bad))
print(f"PASS: {len(skills)} SKILL.md files have valid frontmatter")
PY
```

Then confirm OpenCode itself lists every configured pack as a project skill:

```bash
opencode debug skill > /tmp/argus-loaded-skills.json

python3 - <<'PY'
import json
from pathlib import Path
import yaml

packs = yaml.safe_load(Path(".argus.yml").read_text())["packs"]
loaded = {
    s["name"]: s.get("location", "")
    for s in json.loads(Path("/tmp/argus-loaded-skills.json").read_text())
}
root = str(Path(".opencode/skills").resolve())
missing = [p for p in packs if p not in loaded]
wrong = [p for p in packs if p in loaded and not loaded[p].startswith(root)]
if missing or wrong:
    raise SystemExit(f"FAIL: missing={missing} wrong_location={wrong}")
print(f"PASS: OpenCode loaded all {len(packs)} Argus skills")
PY
```

Finally prove the `skill` tool actually runs in a fresh session (this probe is not
part of the timed comparison):

```bash
MODEL="${MODEL:-openrouter/deepseek/deepseek-v4.1-flash-1017}"
opencode run --auto -m "$MODEL" --format json --dir "$PWD" \
  "Call the skill tool with name 'tdd'. Do not answer from memory. Then reply with only the word ok." \
  > /tmp/argus-skill-smoke.json 2>/tmp/argus-skill-smoke.err

python3 - <<'PY'
import json
from pathlib import Path

raw = Path("/tmp/argus-skill-smoke.json").read_text()
events = [json.loads(line) for line in raw.splitlines() if line.strip()]
if not any(
    e.get("type") == "tool_use" and (e.get("part") or {}).get("tool") == "skill"
    for e in events
):
    raise SystemExit("FAIL: the skill tool was not called")
if '"name":"tdd"' not in raw:
    raise SystemExit("FAIL: the tdd skill was not loaded")
print("PASS: skill tool ran and loaded the tdd skill")
PY
```

Do not start the Run B clock until all three checks pass. If they fail, fix the
frontmatter or config and re-run `argus generate` / `opencode debug skill` before
continuing.

#### B2.6 Commit the installed skill pack

Commit generated files so they are **not** counted as agent work in Run B:

```bash
git add -A
git commit -m "chore: install argus skill pack"
```

Record the install commit and use it as `START_SHA` in B3.

### B3. Run the same prompt

Run with JSON events so B4 can prove the skill pack was activated. The prompt
and model must be identical to Run A; only the output format differs.

```bash
START_SHA=$(git rev-parse HEAD)

start=$(date +%s)
opencode run --auto -m "$MODEL" --format json --dir "$PWD" \
  "$(cat /tmp/compare-prompt.txt)" > /tmp/run-b-events.jsonl 2>/tmp/run-b-agent.log
end=$(date +%s)
```

`MODEL` is the same value used in B2.5 (e.g.
`openrouter/deepseek/deepseek-v4.1-flash-1017`).

After the agent finishes:

```bash
echo "Run B seconds: $((end - start))"
echo "Run B commits: $(git rev-list --count "$START_SHA"..HEAD)"
git diff --stat "$START_SHA"..HEAD
git status --porcelain
```

Preserve evidence:

```bash
git bundle create /tmp/run-b.bundle --all
git log --oneline "$START_SHA"..HEAD > /tmp/run-b-commits.txt
```

### B4. Verify the skill pack was actually activated (required)

A run only measures the skill pack if the agent actually invoked it. If no
`skill` tool call appears, the run is invalid regardless of test results: fix
activation (see the mandatory wording in B2.4), reset to the install commit,
and repeat Run B.

```bash
python3 - <<'PY'
import json
from pathlib import Path

events = [
    json.loads(line)
    for line in Path("/tmp/run-b-events.jsonl").read_text().splitlines()
    if line.strip()
]
calls = [
    e for e in events
    if e.get("type") == "tool_use" and (e.get("part") or {}).get("tool") == "skill"
]
if not calls:
    raise SystemExit(
        "FAIL: Run B never invoked the skill tool; the run did not exercise the pack"
    )
names = [
    ((e.get("part") or {}).get("state") or {}).get("input", {}).get("name")
    for e in calls
]
required = {"tdd", "atomic-commit"}
missing = sorted(required - {n for n in names if n})
if missing:
    raise SystemExit(f"FAIL: Run B did not load required skill(s): {missing}")
print(f"PASS: Run B invoked {len(calls)} skill(s): {names}")
PY
```

Record the loaded pack names with the results. The check requires `tdd` and
`atomic-commit`; loading `pre-commit` as well is expected.

---

## Results Template

Fill in after both runs, then write the filled template to a new timestamped file
in the workspace root. Never overwrite an existing results file.

```bash
RUN_TS="$(date +%Y%m%d-%H%M%S)"
RESULTS_FILE="/home/tsudonymn/code-agent/compare-results-${RUN_TS}.md"
test ! -e "$RESULTS_FILE" || { echo "FAIL: $RESULTS_FILE exists"; exit 1; }
```

File name format: `compare-results-YYYYMMDD-HHMMSS.md` (local time, 24-hour clock).
Capture the timestamp once, when the results file is written, and reuse it for the
whole file. The file header must include:

- Run timestamp (ISO 8601 with local offset, e.g. `2026-11-04T22:30:00-05:00`)
- Kata repo, baseline SHA, Run A start SHA and end SHA, Run B start SHA and end SHA
- Model ID and the prompt source (`compare-skill.md`, "The Prompt" section)

Then the results table, process observations, and analysis follow as in the
template below.

| Metric | Run A (baseline) | Run B (skills) | Delta |
| --- | --- | --- | --- |
| Wall-clock time (s) | | | |
| Agent commits | | | |
| Tests passing (y/n) | | | |
| Skill activated (y/n) | n/a | | |
| Files changed | | | |
| Lines +/- | | | |
| Final tree clean | | | |
| Any goal deviations | | | |

---

## Comparison / Analysis

Compare the two runs on:

1. **Primary:** time to completion and number of commits.
2. **Correctness:** did all tests pass? Any spec edge cases missed (Sulfuras,
   backstage pass drops, Conjured, quality clamps)?
3. **Process:** did the agent add tests, refactor, or only patch conditionals?
4. **Skill influence:** where the runs diverged, and whether the difference is
   attributable to the skill pack vs. run-to-run variance.

**Caveat:** a single run per condition is anecdotal. If feasible, repeat each
condition 2–3 times and report medians; isolate skill install time from agent time.

---

## Execution Checklist

- [ ] Set `main` / `baseline` to `ehei/GildedRose-Refactoring-Kata` `main`
- [ ] Run Preflight: on `main`, at `baseline`, clean tree, **no skill pack installed**, and no Argus/skill reference in `AGENTS.md`
- [ ] If skill pack detected: ask user to uninstall, then re-run Preflight
- [ ] Run A: time, run prompt, count commits, save bundle/log
- [ ] Run Preflight again: reset to `baseline`, verify still on `main` and no skill pack
- [ ] Install Argus (`pip install argus-standards`) with all packs/platforms
- [ ] Verify Argus (`--version`, `validate`, `packs list`, `platforms list`, `generate --check`)
- [ ] Ensure `AGENTS.md` advertises the Argus skills as mandatory (marked `argus:skills` block)
- [ ] Verify OpenCode loaded and can run every Argus skill (frontmatter, `opencode debug skill`, smoke test)
- [ ] Commit generated skill-pack files as the Run B start point (excluded from timing/commit count)
- [ ] Run B: time, run same prompt, count commits, save bundle/log
- [ ] Verify Run B actually invoked the `skill` tool (B4); if not, re-run before trusting the result
- [ ] Fill Results table
- [ ] Write timestamped results file `compare-results-YYYYMMDD-HHMMSS.md` in the workspace root
- [ ] Write comparison conclusion

---

## Results (actual run — Java-pinned rerun)

Executed 2026-11-04. The workspace root is a harness repo, so the kata repo used
was `./GildedRose-Refactoring-Kata` (pinned to `ehei/GildedRose-Refactoring-Kata`
`main`, baseline `d640790`). Both runs used the same model
(`openrouter/deepseek/deepseek-v4.1-flash-1017`) and the updated prompt that pins
the Java implementation, with a clean tree (`git reset --hard baseline &&
git clean -fdx`) before starting the clock. The Run B Argus install commit
(`e520a3f`) is excluded from Run B's counts.

| Metric | Run A (baseline) | Run B (skills) | Delta |
| --- | --- | --- | --- |
| Wall-clock time (s) | 26 | 152 | +126 s (~5.8x) |
| Agent commits | 1 | 2 | +1 |
| Tests passing (y/n) | yes (Java, 15 tests) | yes (Java, 19 tests) | same |
| Files changed | 2 | 2 | 0 |
| Lines +/- | +145 / -50 | +248 / -54 | +103 / +4 |
| Final tree clean | yes | yes | same |
| Any goal deviations | none | none | same |

Process observations:

- **Run A** made one commit (`aa8f7f7`): refactored
  `GildedRose.updateQuality()` and replaced the placeholder test with 15
  spec-based JUnit tests; verified with `./gradlew test`.
- **Run B** made two commits (`c3338af` feat, `1c6d76a` refactor), consistent with
  the `atomic-commit` pack: it added per-item update rules and 19 tests, and ran
  both `./gradlew test` and `./mvnw test`.
- Both runs used Java, removing the earlier language confound.

Comparison:

- With the skill pack, the run took substantially longer (152 s vs 26 s), split the
  change into two commits instead of one, and produced slightly more tests
  (19 vs 15) and a larger diff.
- Both implementations passed the tests independently (`./gradlew test` on each
  result) and covered Sulfuras, backstage tiers, Conjured items, and quality
  clamping; neither deviated from the goal.
- An earlier Java-vs-Python attempt produced the opposite timing result, which
  reinforces that a single run per condition is anecdotal. The direction of the
  timing effect is not stable; the commit-granularity difference is the clearest
  observed skill-pack signal here.

Evidence: `/tmp/run2-a.bundle`, `/tmp/run2-b.bundle`, `/tmp/run2-a-agent.log`,
`/tmp/run2-b-agent.log`, `/tmp/run2-a-commits.txt`, `/tmp/run2-b-commits.txt`;
results also preserved as branches `run-a-java-baseline` (`aa8f7f7`) and
`run-b-java-skills` (`1c6d76a`).
