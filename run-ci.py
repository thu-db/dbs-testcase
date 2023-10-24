import yaml
import sys
import subprocess
import pathlib

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
    if subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=shell).returncode != 0:
        print("Compiled Error!")
        exit(-2)

def run(conf):
    run_cmd = process_commands(conf["commands"])
    cmd = ["python3", "runner.py"]
    if conf["flags"]:
        cmd += ["-f"] + conf["flags"]
    cmd += ["--"] + run_cmd
    subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr,
                    cwd=pathlib.Path(__file__).parent)

if __name__ == "__main__":
    with open(sys.argv[1]) as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)
    compile(conf["compile"])
    run(conf["run"])
