# Tools

These are the scripts tool for Qurrium and Qurecipe

---

## `set_version.py`

Get the version number from the VERSION.txt file and pass it to the environment variable.

- This script is shared with :package:`qurrium` and :package:`qurecipe` repositories.

### Release - `-r`, `--release`

- `stable`

Set version number to the stable version number like `0.x.x` which removed the `dev` part.
And add this version number to the git tag.

Also, when use `stable`, any bump (`-b`, `--bump`) movement except `skip` was not allowed.
It will raise a `ValueError` to terminate workflow.

- `nightly`

Set version number to the stable version number like `0.x.x.devX`.
And add this version number to the git tag.

If you want to bump version, you need to set this flag.

- `check` - the default argument

The versioning checking is used for unit test before the pull request.
Confirm that the version number is still the last version in git version.
Do not modify by develop and ready for bumping version after pull request.

Also, when use `check`, any bump (`-b`, `--bump`) movement except `skip` will take no effect.
It will raise a warning to mention.

### Bump - `-b`. `--bump`

- `skip` - the default argument

Keep current version nummber.

- `dev`

Bump the dev version number. For example, `0.3.1.dev1` to `0.3.1.dev2`.

- `patch`

Bump the patch version number. For example, `0.3.1.dev1` to `0.3.2.dev1`.

- `minor`

Bump the minor version number. For example, `0.3.1.dev1` to `0.4.0.dev1`.

- `major` - Not implemented

This option will raise `NotImplementedError` directly for we consider that it should be done manually.

### Test - `-t`, `--test`

Test script and do nothing on versioning.

---

## `get_version.py` (deprecated)

Get the version number from the VERSION.txt file and pass it to the environment variable.
