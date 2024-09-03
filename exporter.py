import os
import socket
import subprocess
import time
import click
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from typing import Optional

load_dotenv()
console = Console()

# Default values from environment variables
DEFAULT_PGHOST = os.getenv('PGHOST')
DEFAULT_PGPORT = os.getenv('PGPORT', '5432')  # Default PostgreSQL port
DEFAULT_PGUSER = os.getenv('PGUSER')
DEFAULT_PGPASSWORD = os.getenv('PGPASSWORD')
DEFAULT_PGVERSION = os.getenv('PGVERSION', 'latest')  # Default PostgreSQL version
DEFAULT_SSH_REMOTE_USER = os.getenv('SSH_REMOTE_USER')
DEFAULT_SSH_REMOTE_HOST = os.getenv('SSH_REMOTE_HOST')
DEFAULT_SSH_LOCAL_PORT = os.getenv('SSH_LOCAL_PORT', '5432')  # Default local SSH port


def wait_for_port(port: int, host: str = 'localhost', timeout: float = 60.0) -> bool:
    """Checks if a specified port on a host is open within a given timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(1)
    console.print("[green]Timeout: SSH tunnel could not be established.")
    return False


@click.command()
@click.option('--dumpfile', default=None, help='Filename for the dump file')
@click.option('--dbname', required=True, help='Database name to dump')
@click.option('--pghost', default=DEFAULT_PGHOST, help='PostgreSQL host')
@click.option('--pgport', default=DEFAULT_PGPORT, help='PostgreSQL port')
@click.option('--pguser', default=DEFAULT_PGUSER, help='PostgreSQL user')
@click.option('--pgpassword', default=DEFAULT_PGPASSWORD, help='PostgreSQL password')
def cli(dumpfile: Optional[str], dbname: str, pghost: str, pgport: str, pguser: str, pgpassword: str):
    if dumpfile is None:
        dumpfile = f"{dbname}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.dump"
    else:
        dumpfile += ".dump"

    ssh_command: str = (
        f"ssh -L {DEFAULT_SSH_LOCAL_PORT}:{pghost}:{pgport} "
        f"-N -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=no "
        f"{DEFAULT_SSH_REMOTE_USER}@{DEFAULT_SSH_REMOTE_HOST}"
    )

    ssh_proc = subprocess.Popen(ssh_command, shell=True)
    console.print(f"[green]SSH tunnel established with PID[/] [blue]{ssh_proc.pid}")

    if not wait_for_port(int(DEFAULT_SSH_LOCAL_PORT)):
        console.print("[green]Failed to establish a connection through the SSH tunnel.")
        ssh_proc.terminate()
        return

    dump_command: str = (
        f"docker run --rm -v $(pwd):/dumps -e PGPASSWORD='{pgpassword}' postgres:{DEFAULT_PGVERSION} "
        f"pg_dump -h host.docker.internal -p {DEFAULT_SSH_LOCAL_PORT} -U {pguser} "
        f"--format=c --blobs --clean --if-exists --create --no-owner --no-privileges --verbose "
        f"-f /dumps/{dumpfile} {dbname}"
    )

    try:
        console.print("[green]Starting database dump...")
        subprocess.run(dump_command, shell=True, check=True)
        console.print("[green]Database dump completed successfully.")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error during database dump: {e}")
    finally:
        ssh_proc.terminate()
        ssh_proc.wait()
        console.print("[green]SSH tunnel closed.")


if __name__ == '__main__':
    cli()
