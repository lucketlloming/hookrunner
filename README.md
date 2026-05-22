# hookrunner

Lightweight git hook manager that supports per-branch hook configurations.

---

## Installation

```bash
pip install hookrunner
```

Or install from source:

```bash
pip install git+https://github.com/yourusername/hookrunner.git
```

---

## Usage

Initialize hookrunner in your repository:

```bash
hookrunner init
```

Define your hooks in `.hookrunner.yml` at the project root:

```yaml
hooks:
  pre-commit:
    default:
      - run: pytest tests/
    main:
      - run: pytest tests/ --cov
      - run: black --check .
  pre-push:
    default:
      - run: echo "Pushing branch..."
```

Install the hooks into your local `.git/hooks` directory:

```bash
hookrunner install
```

Now your configured hooks will run automatically on the matching branch. If no branch-specific config is found, hookrunner falls back to the `default` configuration.

To list currently installed hooks:

```bash
hookrunner list
```

---

## Configuration

| Key | Description |
|-----|-------------|
| `hooks.<hook>.<branch>` | Commands to run for a specific branch |
| `hooks.<hook>.default` | Fallback commands for any unmatched branch |

---

## License

MIT © [Your Name](https://github.com/yourusername)