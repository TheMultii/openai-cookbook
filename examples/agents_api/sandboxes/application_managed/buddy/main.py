# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openai>=3.13.0",
#     "buddy-sandbox-sdk @ git+https://github.com/buddy/sandbox-sdk-python",
# ]
# ///

"""Run an Agents API task in a Buddy sandbox and clean up both resources."""

import asyncio
import os
import shlex

from buddy_sandbox import Sandbox
from openai import AsyncOpenAI

WORKSPACE = "/buddy"
BRIEF = "Migrate a synchronous Python service to async without changing its API.\n"

SETUP = "sudo npm install -g @openai/codex@alpha"


async def main() -> None:
    executor_key = os.environ["OPENAI_EXECUTOR_API_KEY"]
    async with AsyncOpenAI(timeout=360) as client:
        session = await client.beta.agents.sessions.create(
            agent={"model": "gpt-5.6-sol"},
            environment={"type": "self_hosted", "workspace_directory": WORKSPACE},
        )
        sandbox = None
        print(f"Session: {session.id}", flush=True)
        try:
            assert session.environment.type == "self_hosted"
            executor = shlex.join(
                [
                    "codex",
                    "exec-server",
                    "--remote",
                    session.environment.remote_url,
                    "--environment-id",
                    session.environment.id,
                ]
            )
            async with asyncio.timeout(360):
                suffix = session.id[-12:].lower()
                sandbox = await Sandbox.create(
                    name=f"agents-api-{suffix}",
                    identifier=f"agents_api_{suffix}",
                    os="ubuntu:24.04",
                    first_boot_commands=SETUP,
                    tags=["agents-api"],
                    timeout=600,
                )
                print(f"Sandbox: {sandbox.data.id}", flush=True)
                await sandbox.fs.upload_file(BRIEF.encode(), f"{WORKSPACE}/brief.txt")

                await sandbox.run_command(
                    command=(
                        f"cd {WORKSPACE} && "
                        f"CODEX_API_KEY={shlex.quote(executor_key)} exec {executor}"
                    ),
                    detached=True,
                    stdout=None,
                    stderr=None,
                )

                async with client.beta.agents.sessions.stream(
                    session.id,
                    input="Read brief.txt and write a five-step migration plan to plan.md.",
                ) as events:
                    async for event in events:
                        if event.type in {
                            "error",
                            "agent.session.environment.failed",
                            "agent.session.failed",
                            "agent.session.turn.failed",
                            "agent.session.turn.cancelled",
                        }:
                            raise RuntimeError(f"Agent failed: {event.type}")
                        if event.type == "agent.session.turn.output_text.delta":
                            print(event.delta, end="", flush=True)

                plan = (await sandbox.fs.download_file(f"{WORKSPACE}/plan.md")).decode("utf-8")
                if not plan.strip():
                    raise RuntimeError("The agent did not write a migration plan")
                print(f"\n\nplan.md:\n{plan}")
        finally:
            try:
                if sandbox is not None:
                    async with asyncio.timeout(30):
                        await sandbox.destroy()
            finally:
                async with asyncio.timeout(30):
                    await client.beta.agents.sessions.delete(session.id)


if __name__ == "__main__":
    asyncio.run(main())
