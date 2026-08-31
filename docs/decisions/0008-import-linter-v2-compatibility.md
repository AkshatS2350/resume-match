# 0008 — `import-linter` 2.1 compatibility

Status: accepted

The M0 import-boundary contracts use the syntax and target forms supported by the
pinned `import-linter==2.1` without changing D-01, D-02, the deny-by-default egress
model, `allow_indirect_imports = False`, or the two egress enclaves.

`root_packages` and every multi-value module field use multiline INI lists. External
submodule targets use the narrowest supported top-level target: `urllib`, `http`, and
`google` cover the prior `urllib.request`, `http.client`, and `google.generativeai`
targets respectively. This is intentionally stricter, not an exception.

Future-only enclave, gateway, composition, sanitizer, and job-store ignore entries use
`unmatched_ignore_imports_alerting = none`. This permits scaffolding before those
modules exist; matching forbidden imports remain contract failures.

`resumematch.job.requirements` is created in M0 as an empty architectural boundary so
the scoring-determinism contract remains scoped to requirement extraction. It does not
authorize RM-REQX implementation and avoids incorrectly constraining all of
`resumematch.job`.

The D-09 sanitization-record capability is not an import-linter contract. With
`source_modules = resumematch`, import-linter 2.1 rejects the required forbidden
contract because the source root is an ancestor of `resumematch.core.session_write`
and the modules have shared descendants. Replacing it with a broader exception would
leave sibling modules in `core` unprotected. The dedicated static checker
`tools/check_session_write_boundary.py` therefore enforces the exact invariant: only
`resumematch.privacy.sanitizer` may import or literally dynamically import
`resumematch.core.session_write`. The private mutation capability and Task 3.8
runtime/unit coverage complete D-09's defense in depth.
