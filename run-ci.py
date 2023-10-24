import sys
import subprocess
import pathlib
import os
import hashlib

import yaml



def process_commands(cmd):
    if isinstance(cmd, str):
        if "'" in cmd or '"' in cmd:
            print(r"One-line string style commmands does not support ['] or [\"]")
            exit(-1)
        cmd = cmd.split()
    assert isinstance(cmd, list)
    return cmd

def compile(conf):
    cmd = conf["commands"]
    shell = isinstance(cmd, str)
    print("compile commands:", cmd)
    if subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=shell).returncode != 0:
        print("Compiled Error!")
        exit(-2)

def run(conf):
    run_cmd = process_commands(conf["commands"])
    cmd = ["python3", "runner.py"]
    if conf["flags"]:
        cmd += ["-f"] + conf["flags"]
    cmd += ["--"] + run_cmd
    print("run checker commands:", cmd)
    user_prog_cwd = os.getcwd()
    env = os.environ.copy()
    env["USER_PROG_CWD"] = user_prog_cwd
    subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr,
                    cwd=pathlib.Path(__file__).parent, env=env)

if __name__ == "__main__":
    with open("./.gitlab-ci.yml", "rb") as file:
        h = hashlib.sha1(file.read()).hexdigest()
        assert h == "7c840922c78d83339ad7a76b302288e18a9545b2"
    with open("./testcase.yml") as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)
    compile(conf["compile"])
    run(conf["run"])
