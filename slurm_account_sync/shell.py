import logging
import subprocess
from typing import List
import shlex

logger = logging.getLogger(__name__)


def execute_command(cmd: List[str], dry_run=False, hide_log=False) -> str:
    sacctmgr_cmd = subprocess.check_output(["which", "sacctmgr"]).decode("utf8").strip()

    cmd = cmd.replace("$(which sacctmgr)", sacctmgr_cmd)

    if not hide_log:
        logger.info(cmd)
    if dry_run:
        return None
    result = subprocess.run(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
    )
    stdout = result.stdout.decode().splitlines()
    stderr = result.stderr.decode()
    if stderr:
        raise Exception(stderr)
    return stdout
