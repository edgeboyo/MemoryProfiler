import argparse
from concurrent.futures import process
from time import sleep
import psutil

unitModifiers = {'B': 0, "KB": 1, 'MB': 2, "GB": 3}


def checkMemory(pid, unit='MB'):

    unitModifier = unitModifiers[unit]

    process = psutil.Process(pid)

    memory = process.memory_info().rss

    for proc in process.children(recursive=True):
        memory += proc.memory_info().rss

    return memory / 1024 ** unitModifier


def runProcess(command):
    import sys
    import subprocess

    pipe = subprocess.Popen(command, stdout=sys.stdout,
                            stderr=sys.stderr, shell=True)

    print(f"Process {pipe.pid} started...")

    return pipe.pid


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a command, collect its memory usage information and print its average")
    parser.add_argument("command", metavar='command', type=str,
                        nargs="+", help="Command to execute and profile")
    parser.add_argument("-u", "--units", dest="units", type=str,
                        default="MB", help="Select memory units to log")
    parser.add_argument("-t", "--time", dest="time", type=float,
                        default=.25, help="Select time between measurements")
    parser.add_argument("-m", "--monitor", dest="monitor", action="store_true",
                        help="Output the current usage on every iteration")
    args = parser.parse_args()

    command = args.command
    units = args.units.upper()
    time = args.time
    monitor = args.monitor

    if units + "B" in unitModifiers:
        units += "B"
    elif units not in unitModifiers:
        print(f"{units} not a supported unit")
        exit(2)

    return (command, units, time, monitor)


if __name__ == "__main__":
    (command, units, time, monitor) = parse_args()

    processPid = runProcess(command)

    iterations = 0
    memoryUsages = 0

    try:
        while True:
            mem = checkMemory(processPid, units)
            if monitor:
                print(
                    f"[#{iterations + 1}] Current memory use is {'%.3f' % mem} {units}")
            memoryUsages += mem
            iterations += 1
            sleep(time)
    except psutil.NoSuchProcess as e:
        print("-" * 72)
        print(
            f"Process {processPid} & its children concluded with an average use of {'%.3f' % (memoryUsages / iterations)} {units}")
    except Exception as e:
        print("Unknown error occurred: ")
        print(e)

        exit(1)
