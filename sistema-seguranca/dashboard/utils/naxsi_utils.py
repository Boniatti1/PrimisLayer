import subprocess

WHITELIST_PATH = "/etc/nginx/generated.wl"
NAXSI_LOGPATH = "/var/log/nginx/normal_error.log"
NXUTIL_PATH = "/opt/nxutil/nx_util.py"
MAIN_RULES = "/etc/nginx/naxsi.rules"


def get_naxsi_whitelist():
    with open(WHITELIST_PATH, "r") as f:
        return f.readlines()


def get_naxsi_rules():
    with open(MAIN_RULES, "r") as f:
        return f.readlines()


def learning_mode_active():
    rules = get_naxsi_rules()
    if any("LearningMode;" in line for line in rules):
        return True
    return False


def activate_learning_mode():
    rules = get_naxsi_rules()
    if any("LearningMode;" in line for line in rules):
        raise Exception("Learning mode já ativado")
    
    rules.insert(0, "LearningMode;\n")
    
    with open(MAIN_RULES, "w") as f:
        f.writelines(rules)
    
    nginx_reload()


def deactivate_learning_mode():
    rules = get_naxsi_rules()
    rules = [line for line in rules if "LearningMode;" not in line]

    with open(MAIN_RULES, "w") as f:
        f.writelines(rules)

    nginx_reload()
    

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

    nginx_reload()


def nginx_reload():
    subprocess.run(
        ["supervisorctl", "restart", "nginx"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )