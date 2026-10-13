# GitHub sync readiness, 2026-10-13

Two repositories, two different states. Recorded because "the project can be synced
cleanly" was the stated goal, and one of the two cannot be synced at all.

---

## 1. LIMEN — ready

| | |
|---|---|
| remote | `https://github.com/Computational-social-science/LIMEN.git` |
| local tip | `36c1695` |
| remote tip | `6d06d2a` |
| **`git push --dry-run origin main`** | **succeeds** — `6d06d2a..36c1695  main -> main`, exit 0 |

The dry run is the real check: it performs the negotiation and the object transfer
without updating the ref, so a size rejection or a missing remote surfaces here
rather than after the work looks finished.

## 2. keystroke-observatory — RESOLVED 2026-10-14

| | |
|---|---|
| remote | `https://github.com/limen-research/keystroke-observatory.git` |
| recorded remote | `https://github.com/limen-research/keystroke-observatory.git` — **the org does not exist** (404) |
| **now points at** | `https://github.com/Computational-social-science/keystroke-observatory` |
| visibility | **private** — publication is a separate, irreversible decision |
| **`git push origin main`** | **succeeds** — `a20a71a..37c57d0  main -> main` |
| `git ls-remote origin` | same failure, so the repository does not exist at that URL |

**This is not a credential or network problem.** LIMEN's dry run to a different
GitHub org succeeded in the same session, so the transport works. The specific
repository is absent.

**The URL is recorded in exactly one place: this clone's `.git/config`.** It appears
in no project file — not `README.md`, not `pyproject.toml`, not `package.json`, not
the CI workflow. So the intended destination cannot be recovered from the project
itself; it exists only on this machine, and a fresh clone would carry a remote
nobody chose deliberately.

**Resolved.** The owner's instruction was that keystroke-observatory syncs to GitHub
as an independent repository, so it was created under the account the available
credential can write to, and pushed. The three options that were open:

1. **Create `limen-research/keystroke-observatory`** and push. Keeps the URL as
   recorded, and matches the project's independent status.
2. **Point it at an existing repository** — e.g. under the same
   `Computational-social-science` org as LIMEN. Contradicts the independence
   decision unless the project is meant to be a satellite.
3. **Publish nowhere yet.** The project is then local-only, which is a legitimate
   answer, but it should be recorded as a choice rather than left as a dangling
   remote that fails on first use.

The URL is now written into the project — `README.md` states it with the visibility,
and the dashboard project's `keystroke-observatory/pyproject.toml` `[project.urls]` is restored. v1 had that section and v2
dropped it, which is precisely why the destination had existed only in one clone's
`.git/config` and could not be reconstructed from the repository itself.

## 3. What is now sync-safe in both

- **No file over the size limit.** `check_repo_size.py` reports 0 objects over the
  50 MB threshold against GitHub's 100 MB hard limit, with its negative control
  firing. The 153 MB derived Parquet is excluded by `.gitignore` in **both**
  repositories — it was staged twice during this work, once in each, and would have
  failed at `push` both times.
- **The dashboard is self-contained.** Its
  `keystroke-observatory/scripts/check_standalone_clone.py` clones it to a
  directory with no sibling project and requires that the clone carries all five
  evidence files, that the handoff gate runs there without FAIL, and that no script
  reaches through the parent for evidence it owns.
- **No dangling paths.** Both repositories' guards pass, including the anchor guard
  that checks every documented path resolves.

## 4. The relationship between the two, as it now stands

```
LIMEN  (Computational-social-science/LIMEN)
  ├── its own science: reads the raw corpus directly
  ├── cites keystroke-observatory's findings in docs/ and CURRENT_OBJECT.md
  └── does NOT contain the keystroke pipeline, its data, or its evidence

keystroke-observatory  (remote: unresolved)
  ├── owns the pipeline, the v2 data, the v1 evidence archive
  ├── INPUT defaults reach the enclosing checkout (corpus, built Parquet,
  │   pipeline) and are documented and overridable
  └── reaches nothing in LIMEN for anything it owns
```

The dependency is one-way: LIMEN consumes the dashboard's findings; the dashboard
consumes only raw inputs. On disk the dashboard happens to sit inside the LIMEN
checkout, which is a convenience of this machine, not a structural fact — which is
why the standalone-clone guard exists.
