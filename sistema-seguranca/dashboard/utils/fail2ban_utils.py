from datetime import datetime
from pathlib import Path


FAIL2BAN_LOG_PATH = "/var/log/fail2ban-actions.log"


def parse_fail2ban_log(line):
    parts = line.strip().split(" - ")

    time_str, failures, ip, name, msg = parts
    msg = parts[4] if len(parts) > 4 else ""

    timestamp = datetime.fromtimestamp(int(time_str)).strftime("%Y-%m-%d %H:%M:%S")

    return {"time": timestamp, "failures": failures, "ip": ip, "name": name, "msg": msg}


def get_fail2ban_logs(lines=100):
    with open(FAIL2BAN_LOG_PATH, "r") as f:
        logs = f.readlines()[-lines:][::-1]

    formatted_logs = []
    for line in logs:
        formatted_logs.append(parse_fail2ban_log(line))

    return formatted_logs
