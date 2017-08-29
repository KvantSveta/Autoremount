import signal
from time import sleep
from subprocess import check_output, call
from threading import Event

from logger import Logger


__author__ = "Evgeny Goncharov"


def check_is_mount(log):
    answer = check_output(["ls", "-al", "/media"])
    answer = answer.decode()
    answer = answer.splitlines()
    # [
    #     'total 8',
    #     'drwxr-xr-x  2 root root 4096 Jun 21 17:44 .',
    #     'drwxr-xr-x 17 root root 4096 Aug 14 07:26 ..'
    # ]
    if len(answer) == 3:
        log.error("Device unmount")
        sleep(1)
        return False
    else:
        #log.info("Device mount")
        sleep(10)
        return True


def decorator(func):
    def wrapper(log, run_service, param=""):
        try:
            func(param)
            sleep(1)
        except Exception as e:
            log.error("Error: {}".format(e))
            run_service.clear()
    return wrapper


@decorator
def call_mount(param=""):
    call(["mount", "/media"])


@decorator
def call_umount(param=""):
    device = check_output(
        ["blkid", "-U", "7e0e1084-33bf-44f8-8796-d67ed6200bad"]
    )
    device = device.decode()
    device = device.strip()
    # /dev/sda1 or /dev/sdb1
    call(["umount", device, param])


log = Logger("/home/pi/Autoremount/detect.log")
log.info("Program start")

run_service = Event()
run_service.set()


def handler(signum, frame):
    run_service.clear()
    log.info("Signal to stop service {}".format(signum))


signal.signal(signal.SIGTERM, handler)

while run_service.is_set():
    if check_is_mount(log):
        continue

    log.info("Check simple mount")
    call_mount(log, run_service)

    if check_is_mount(log) or not run_service.is_set():
        continue

    log.info("Check middle mount")
    call_umount(log, run_service)
    call_mount(log, run_service)

    if check_is_mount(log) or not run_service.is_set():
        continue

    log.info("Check hard mount")
    call_umount(log, run_service, "-l")
    call_mount(log, run_service)

    if check_is_mount(log) or not run_service.is_set():
        continue

    log.critical("Nothing works!!!")
    run_service.clear()

log.info("Program stop\n")
