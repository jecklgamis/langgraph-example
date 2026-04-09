import os
import shlex
import subprocess
from os import listdir


def read_file(file: str) -> str:
    """Reads a file and returns its content"""
    try:
        with open(file, "rt") as f:
            return f.read()
    except Exception as e:
        return f"Unable to read file {file}: {e}"


def list_files(directory: str) -> str:
    """List files in a given directory"""
    try:
        return "\n".join(listdir(directory))
    except Exception as e:
        return f"Unable to list files in {directory}: {e}"


def run_ifconfig(arguments: str) -> str:
    """The ifconfig utility is used to assign an address to a network interface and/or configure network interface parameters."""
    try:
        safe_args = " ".join(shlex.quote(arg) for arg in shlex.split(arguments))
        return subprocess.run(
            f"ifconfig {safe_args}", shell=True, capture_output=True, text=True
        ).stdout
    except Exception as e:
        return f"Unable to run ifconfig {arguments}: {e}"


def run_netstat(arguments: str) -> str:
    """The netstat command symbolically displays the contents of various network-related data structures.  There are a number of output formats, depending on the options for the information presented.  The first form of the command displays a list of active sockets for each
    protocol.  The second form presents the contents of one of the other network data structures according to the option selected. Using the third form, with a wait interval specified, netstat will continuously display the information regarding packet traffic on the configured
    network interfaces.  The fourth form displays statistics for the specified protocol or address family. If a wait interval is specified, the protocol information over the last interval seconds will be displayed.  The fifth form displays per-interface statistics for the
    specified protocol or address family.  The sixth form displays mbuf(9) statistics.  The seventh form displays routing table for the specified address family.  The eighth form displays routing statistics."""
    try:
        safe_args = " ".join(shlex.quote(arg) for arg in shlex.split(arguments))
        return subprocess.run(
            f"netstat {safe_args}", shell=True, capture_output=True, text=True
        ).stdout
    except Exception as e:
        return f"Unable to run netstat {arguments}: {e}"


def run_df(arguments: str) -> str:
    """Run the Unix df command to get free disk space. arguments is a space-separated string of flags and paths, e.g. '-h /tmp'"""
    try:
        safe_args = " ".join(shlex.quote(arg) for arg in shlex.split(arguments))
        return subprocess.run(
            f"df {safe_args}", shell=True, capture_output=True, text=True
        ).stdout
    except Exception as e:
        return f"Unable to run df {arguments}: {e}"


def run_du(arguments: str) -> str:
    """Run the Unix du command to display disk usage statistics"""
    try:
        safe_args = " ".join(shlex.quote(arg) for arg in shlex.split(arguments))
        return subprocess.run(
            f"du {safe_args}", shell=True, capture_output=True, text=True
        ).stdout
    except Exception as e:
        return f"Unable to run du {arguments}: {e}"


def get_current_user() -> str:
    """Returns the current logged-in username."""
    return (
        os.getenv("USER") or os.getenv("USERNAME") or os.popen("whoami").read().strip()
    )


def run_hostname() -> str:
    """Get the hostname of this machine"""
    return subprocess.run("hostname", capture_output=True, text=True).stdout.strip()
