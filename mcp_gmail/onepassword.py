import subprocess


def _op(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["op"] + args, capture_output=True, text=True)


def read_field(vault: str, item: str, field: str) -> str | None:
    result = _op(["read", f"op://{vault}/{item}/{field}"])
    return result.stdout.strip() if result.returncode == 0 else None


def write_field(vault: str, item: str, field: str, value: str) -> None:
    # Try updating existing item first; if it doesn't exist, create it.
    result = _op(["item", "edit", item, "--vault", vault, f"{field}[password]={value}"])
    if result.returncode != 0:
        subprocess.run(
            ["op", "item", "create",
             "--category", "Secure Note",
             "--title", item,
             "--vault", vault,
             f"{field}[password]={value}"],
            check=True,
        )
