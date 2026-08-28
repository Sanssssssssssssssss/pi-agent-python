# Pi Agent for Python release process

The package is published to PyPI as `pi-agent-python`. A normal merge to `main` never
publishes a package.

## Release gate

1. Confirm the GitHub and PyPI names are still available or owned by this project.
2. Set the version in `pyproject.toml` and refresh `uv.lock`.
3. Run the full Linux and Windows CI checks.
4. Build wheel and sdist, then clean-install and smoke-test both artifacts.
5. Complete one sanitized real-provider one-shot smoke. Deterministic offline tests are
   necessary but do not replace this end-to-end check.
6. Configure a PyPI Pending Trusted Publisher for this repository, the `release.yml`
   workflow, and the `pypi` environment.
7. Publish a GitHub Release tagged `v<version>`. The release workflow verifies the
   artifacts, attaches them to the release, and sends the same files to PyPI using OIDC.
8. Verify a clean PyPI install can import `pi_ai`, `pi_agent`, and `pi_coding`, and run
   `pi-agent --version` and `pi-agent --help`.

PyPI files are immutable. Never reuse a version after any artifact for it has been
uploaded.
