# CHANGELOG

<!-- version list -->

## v1.1.0 (2026-07-31)

### Bug Fixes

- **lint**: Remove quoted forward-reference type annotation (ruff UP037)
  ([`d031d51`](https://github.com/bipinkapri-git/PerfumeScanner/commit/d031d5178c2a8430c61e7e53712837c0098a281a))

### Chores

- Standardize assets/ into images/ and audio/ subfolders
  ([`cb79ab4`](https://github.com/bipinkapri-git/PerfumeScanner/commit/cb79ab44ae5a6161dd8f9093c062c39d30750716))

### Features

- Add typo-tolerant search autocomplete
  ([`e05ef8d`](https://github.com/bipinkapri-git/PerfumeScanner/commit/e05ef8db12a23f1e5fa1e12368420b55a417501d))

- Play a sound effect + clearer message when no products match
  ([`4601169`](https://github.com/bipinkapri-git/PerfumeScanner/commit/4601169c6f4b4dc70eaed4c3f4c3f72289f61278))


## v1.0.3 (2026-07-30)

### Bug Fixes

- **lint**: Remove unused noqa directive and use module logger
  ([`6d78f5c`](https://github.com/bipinkapri-git/PerfumeScanner/commit/6d78f5c7fcfe9e67d2bcbb215e0025ec0149467d))

- **scraper**: Resolve S110 and BLE001 by catching explicit exception tuple and adding debug logging
  ([`073aaad`](https://github.com/bipinkapri-git/PerfumeScanner/commit/073aaad93f03c6e5da96c9cf5926b0cebe870018))

- **scraper**: Safeguard DOM link attribute parsing against AttributeError
  ([`1f6d148`](https://github.com/bipinkapri-git/PerfumeScanner/commit/1f6d148bfbe5abf2e0384da0a188a6dc6d227992))


## v1.0.2 (2026-07-30)

### Bug Fixes

- **main**: Handle Streamlit Cloud runtime context to avoid duplicate initialization error
  ([`a269170`](https://github.com/bipinkapri-git/PerfumeScanner/commit/a26917025381b773798acfa9fbfb11790832220c))

### Build System

- Add vercel.json configuration for Vercel deployment
  ([`b455ec0`](https://github.com/bipinkapri-git/PerfumeScanner/commit/b455ec046818ef4372ec8a00bd140d688d72a1af))


## v1.0.1 (2026-07-30)

### Bug Fixes

- **comparator, scraper**: Enforce min price threshold and fix linting/formatting
  ([`99945fa`](https://github.com/bipinkapri-git/PerfumeScanner/commit/99945fa5c4b873f5b18be657db810949c78b9053))

- **imports**: Remove unused typing imports and noqa directive
  ([`bdb7dc3`](https://github.com/bipinkapri-git/PerfumeScanner/commit/bdb7dc393fc0658ead0cd15a8c7ab9b1c41e5fb1))

- **lint**: Resolve all 19 ruff linting errors and type annotations
  ([`e10cb91`](https://github.com/bipinkapri-git/PerfumeScanner/commit/e10cb916fee71d064765e4da7eab78370ad627d1))

- **scraper**: Filter rating elements and enforce min price threshold
  ([`c4ac591`](https://github.com/bipinkapri-git/PerfumeScanner/commit/c4ac5916bf89b5819c87a29661a1c7ffc889125e))

- **types, ci**: Update type hints to PEP 585/604 standards and use python -m for CI commands
  ([`79e75ae`](https://github.com/bipinkapri-git/PerfumeScanner/commit/79e75ae00a59bf79dd2617752a87e1f59dd1bb06))

### Continuous Integration

- Add ruff and bandit to dev dependencies and CI install step
  ([`5632e80`](https://github.com/bipinkapri-git/PerfumeScanner/commit/5632e806b10670de727859042b6ea0e4b6fa8c75))

- Add unit test execution and fix/* branch triggers to CI workflow
  ([`2da7b2b`](https://github.com/bipinkapri-git/PerfumeScanner/commit/2da7b2b2c479eef6b3f5395b3cc991e8743cc3a2))

- Deduplicate triggers to prevent duplicate workflow runs on PRs
  ([`33c0aee`](https://github.com/bipinkapri-git/PerfumeScanner/commit/33c0aeec24b6722d0b8971803454b10592ee4b40))

### Documentation

- Update README with active retailer list and correct scraper docstring
  ([`64e4691`](https://github.com/bipinkapri-git/PerfumeScanner/commit/64e46911962ab04c4e2e5a81e637e6d5947ea688))


## v1.0.0 (2026-07-17)

- Initial Release
