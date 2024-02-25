import subprocess
import sys
from pathlib import Path


def start_service(service_path: Path | str, dbus_name: str, unit_name: str,
                  *args):
    cmd = ["systemd-run", "--user", "--service-type=dbus", "--collect",
           f"--unit={unit_name}.service", f"--property=BusName={dbus_name}",
           "python3", str(service_path), *args]
    print("Executing: ", " ".join(cmd), file=sys.stderr)
    try:
        subprocess.check_call(cmd, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        # Print the log of the service
        print("Service log:", file=sys.stderr)
        subprocess.check_call(["/usr/bin/journalctl", "--user",
                               f"-u{unit_name}.service", "--no-pager",
                               "--output=cat"])
        print("Service log end", file=sys.stderr)
        raise


def stop_service(unit_name: str):
    if not is_service_active(unit_name):
        return
    subprocess.check_call(["/usr/bin/systemctl", "--user", "stop",
                           f"{unit_name}.service"])


def is_service_active(unit_name: str) -> bool:
    p = subprocess.run(["/usr/bin/systemctl", "--user", "--quiet", "is-active",
                        f"{unit_name}.service"],
                       check=False)
    return p.returncode == 0


def continuously_print_service_output(unit_name: str) -> subprocess.Popen:
    cmd = ["journalctl", "--user", "-f", f"-u{unit_name}.service", "--no-pager",
           "--output=cat"]
    print(" ".join(cmd), file=sys.stderr)
    return subprocess.Popen(cmd)
