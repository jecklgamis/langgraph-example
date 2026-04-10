import logging
import subprocess

logger = logging.getLogger(__name__)


def run_bash(command: str) -> str:
    """Executes an arbitrary bash command and returns its output."""
    logger.info("Running bash command: %s", command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.returncode != 0:
            output += result.stderr
        return output or f"Command exited with code {result.returncode}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after 30 seconds: {command}"
    except Exception as e:
        return f"Failed to run command '{command}': {e}"
