import os
from pathlib import Path

candidates = [
    Path.home() / ".claude",
    Path.home() / ".config" / "claude",
    Path.home() / ".config" / "claude-code",
    Path.home() / ".local" / "share" / "claude",
    Path.home() / ".anthropic"
]

found = []
for p in candidates:
    if p.exists():
        found.append(str(p))
        # Look for a skills subdir
        if (p / "skills").exists():
            found.append(str(p / "skills"))

print("Found paths:", found)
