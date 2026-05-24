# Variable typo `basic_change_unity_from_opencv` (should be `basis_change_…`)

**Severity**: low — purely cosmetic; consistent typo, math is correct.

**Location**: `packages/python/core/src/core/axis_convention.py:15` defines `basic_change_unity_from_opencv`. The same misspelling is used at lines 16, 23, 24, 30, 31, 36, 45 (within the file). The sibling constant on line 16 is correctly spelled `basis_change_opencv_from_unity`, making the inconsistency obvious.

**Symptom**: None at runtime — the typo'd name resolves wherever it is used because all uses are consistent within the file. Reader confusion only.

**Mechanism**: Typo introduced at the original definition and propagated through internal references.

**Fix sketch**: Rename `basic_change_unity_from_opencv` → `basis_change_unity_from_opencv` throughout `axis_convention.py`. Confirm no external imports (`grep -rn basic_change` across `/placeframe`) — the symbol is module-private in practice. Single-file rename, no codegen.

**Verification**: `grep basic_change /placeframe` returns no hits post-fix; `uv run basedpyright` and `uv run pytest` stay clean.
