import os
import subprocess

import click
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

DOCKER_CONTAINER_NAME = os.getenv('CONTAINER_NAME')  # Default Docker container name
DOCKER_LOCAL_HOST = os.getenv('DOCKER_LOCAL_HOST')
DOCKER_LOCAL_USER = os.getenv('DOCKER_LOCAL_USER')


@click.command()
@click.option('--dumpfile', required=True, help='Path to the dump file')
def cli(dumpfile: str) -> None:
    copy_command: str = (
        f"docker cp {dumpfile} {DOCKER_CONTAINER_NAME}:/tmp/{dumpfile}"
    )

    try:
        console.print("[green]Copying dump file to container...")
        subprocess.run(copy_command, shell=True, check=True)
        console.print("[green]Dump file copied successfully.")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error during file copy: {e}")
        exit(1)

    restore_command: str = (
        f"docker exec -it {DOCKER_CONTAINER_NAME} "
        f"pg_restore --clean --if-exists --create --no-owner --no-privileges --verbose "
        f"-d postgres -h {DOCKER_LOCAL_HOST} -U {DOCKER_LOCAL_USER} /tmp/{dumpfile}"
    )

    try:
        console.print("[green]Starting database restore...")
        subprocess.run(restore_command, shell=True, check=True)
        console.print("[green]Database restore completed successfully.")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error during database restore: {e}")


if __name__ == '__main__':
    cli()
