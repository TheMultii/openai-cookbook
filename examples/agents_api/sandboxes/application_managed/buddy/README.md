# Application-managed Buddy sandbox

The application creates an Agents API session and a [Buddy](https://buddy.works)
sandbox, starts `codex exec-server`, and asks the agent to turn `brief.txt` into
`plan.md`. It prints the plan, destroys the sandbox, and deletes the session.

## Run

Set `BUDDY_TOKEN`, `BUDDY_WORKSPACE`, `BUDDY_PROJECT`, `OPENAI_API_KEY`, and a
separate restricted `OPENAI_EXECUTOR_API_KEY`. The OpenAI keys must have the same
owner, organization, and project. Only the executor key enters the sandbox, and
it is passed inline with the command rather than stored as a sandbox variable.

The Buddy token needs permission to manage sandboxes in the workspace. Without
`BUDDY_PROJECT` the sandbox is created at the workspace level instead.

From the Cookbook repository root:

```bash
uv run examples/agents_api/sandboxes/application_managed/buddy/main.py
```

Dependencies are declared inline. The script allows six minutes for setup and
execution and attempts both cleanup operations on failure. The sandbox also stops
itself after ten idle minutes. If creation times out before returning an ID, check
Buddy for a sandbox named after the printed session ID before retrying.

The agent works in `/buddy`, the directory the sandbox starts in. Node ships with
the image, so the only first-boot command installs `@openai/codex`, and
`Sandbox.create` returns once that setup succeeds.

To skip the install on every run, capture a snapshot of a configured sandbox with
`sandbox.create_snapshot()` and create from it with `Sandbox.create_from_snapshot()`.

For follow-up turns, keep both resources until the application is finished.
Do not attach a provisioning webhook handler to these sessions.

## References

- [Buddy Sandboxes documentation](https://buddy.works/docs/sandboxes)
- [Buddy Sandbox SDK for Python](https://github.com/buddy/sandbox-sdk-python)
