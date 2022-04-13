import os
import sys
import time

def report(progress):
    print("{}%".format(int(progress*100)))


def scan(folder, fraction, report):
    dirs = []
    files = []
    for each in os.listdir(folder):
        path = os.path.join(folder, each)
        if os.path.isdir(path):
            dirs.append(path)
        else:
            files.append(path)

    for d in dirs:
        scan(d, fraction/len(dirs), report)


if __name__ == '__main__':
    scan('.')
