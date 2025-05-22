import subprocess

WHITELIST_PATH = "/etc/nginx/generated.wl"
NAXSI_LOGPATH = "/var/log/nginx/normal_error.log"
NXUTIL_PATH = "/opt/nxutil/nx_util.py"


def get_naxsi_whitelist():
    with open(WHITELIST_PATH, "r") as f:
        return f.readlines()


def get_optimized_rules():
    result = subprocess.run(
        ["python3", NXUTIL_PATH, "-l", NAXSI_LOGPATH, "-o", "-p", "1"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    rules = result.stdout.splitlines()

    return rules


def save_optimized_rules():
    result = get_optimized_rules()

    with open(WHITELIST_PATH, "w") as f:
        for line in result:
            f.write(line + "\n")

    subprocess.run(
        ["supervisorctl", "restart", "nginx"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
