import subprocess


def run_pipeline(cmd, args=None):
    """Runs a pipeline in a child process, allowing each
    pipeline to use its own environment.

    Args:
        cmd (list): command line
        args (dict, optional): Popen args. Defaults to {}.

    Returns: None
    """

    args = {} if not args else args

    return subprocess.Popen(cmd, **args)


if __name__ == "__main__":
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sleep", default=10)
    _args = parser.parse_args()

    logger = logging.getLogger()

    command = ["sleep", str(_args.sleep)]
    RETCODE = run_pipeline(command)

    logger.debug("returncode %s", RETCODE)
