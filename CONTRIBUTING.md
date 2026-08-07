# Contributing

This project preserves a six-milestone evidence history. Contributions should
be narrowly scoped, traceable to the current milestone, and accompanied by
reproducible validation.

Before opening a pull request:

1. Run `python scripts/verify_case.py`.
2. Run `python -m unittest discover -s tests -v`.
3. Run `python scripts/scan_public_boundary.py`.
4. Confirm that generated case artifacts have not drifted with
   `python scripts/generate_case.py --check`.
5. State assumptions, evidence changed, tests run, limitations, and the human
   decision point.

Do not add private Sherizon source code, customer evidence, deployment
credentials, or autonomous external writes.
