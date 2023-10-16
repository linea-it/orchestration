#!/usr/bin/env python3

import time
from tasks import run

params = {
    "pipeline-name": "hello_world",
    "output-dir": "/home/singulani/projects/orchestration/tests",
    "config": {"sleeptime": "20"},
}

NRUNS = 10

lruns = []

for x in range(NRUNS):
    print("Running task " + str(x))
    if x != 5:
        params["id"] = "tests-" + str(x)
    r = run.apply_async([params], ignore_result=True)
    lruns.append(r)

time.sleep(10)
task2 = lruns[3]
task2.revoke(terminate=True, signal="SIGSTOP")

time.sleep(5)
task5 = lruns[6]
task5.revoke(terminate=True, signal="SIGSTOP")
