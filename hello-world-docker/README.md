# Hello World (Docker) Action

A minimal Docker action that echoes a greeting and demonstrates inputs/outputs.

## Usage

```yaml
- name: Hello World (Docker)
  uses: ./hello-world-docker
  with:
    who-to-greet: "Stratus"
```

## Inputs

- `who-to-greet`: Who to greet (default: `World`)

## Outputs

- `time`: The time the greeting was generated (set by writing to `$GITHUB_OUTPUT` in the entrypoint script)

---

## How outputs work in Docker actions

For Docker actions, outputs must be set in the entrypoint script:

```sh
echo "time=$(date)" >> $GITHUB_OUTPUT
```

The `outputs` block in `action.yml` is for documentation only.

---

## When to use Docker Actions

- For custom environments, dependencies, or when you need a consistent runtime.
- Use composite actions for simple logic or combining other actions.

## License

MIT
