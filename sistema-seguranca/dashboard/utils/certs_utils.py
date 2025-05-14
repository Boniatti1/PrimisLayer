import json
import subprocess
from pathlib import Path
from flask import abort, send_file

OPENSSL_PATH = Path("/etc/ssl/server/openssl.cnf")
CLIENTS_PATH = Path("/etc/ssl/server/clients")
CLIENTS_JSON_PATH = CLIENTS_PATH / "clients.json"
CA_PATH = Path("/etc/ssl/server/ca")
CERTS_LOGPATH = "/var/log/certs.log"


def log(path, msg):
    with open(path, "a") as f:
        f.write(str(msg) + "\n")


def list_client_certs():
    try:
        with open(CLIENTS_JSON_PATH, "r") as f:
            reader = json.load(f)
            return reader["clients"]
    except FileNotFoundError:
        log(CERTS_LOGPATH, f"Arquivo {CLIENTS_JSON_PATH} não encontrado. Criando novo")
        with open(CLIENTS_JSON_PATH, "w") as f:
            json.dump({"clients": []}, f)
        return []
    except Exception as e:
        log(CERTS_LOGPATH, f"Erro inesperado ao ler {CLIENTS_JSON_PATH}: {str(e)}")
        return False


def delete_client_cert(name):
    locations: list = list_client_certs()
    if name not in locations:
        return

    client_dir: Path = CLIENTS_PATH / name
    crt_path = client_dir / "client.crt"
    ca_crt = CA_PATH / "ca.crt"
    ca_key = CA_PATH / "ca.key"
    try:
        revoke_resp = subprocess.run(
            [
                "openssl",
                "ca",
                "-revoke",
                str(crt_path),
                "-config",
                str(OPENSSL_PATH),
                "-keyfile",
                str(ca_key),
                "-cert",
                str(ca_crt),
                "-crl_reason",
                "cessationOfOperation",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        log(CERTS_LOGPATH, f"Certificado {name} revogado: {revoke_resp}")

        crl_resp = subprocess.run(
            [
                "openssl",
                "ca",
                "-gencrl",
                "-out",
                str(CA_PATH / "crl.pem"),
                "-config",
                str(OPENSSL_PATH),
                "-keyfile",
                str(ca_key),
                "-cert",
                str(ca_crt),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        log(CERTS_LOGPATH, f"CRL atualizado para certificado {name}: {crl_resp}")

        subprocess.run(["nginx", "-s", "reload"], check=True)

        try:
            for file in client_dir.glob("*"):
                file.unlink()
            client_dir.rmdir()

            locations.remove(name)
            with open(CLIENTS_JSON_PATH, "w") as f:
                json.dump({"clients": locations}, f)

            return True
        except Exception as e:
            log(
                CERTS_LOGPATH,
                f"Erro inesperado ao remover o diretório {client_dir}: {str(e)}",
            )

    except Exception as e:
        log(CERTS_LOGPATH, f"Erro inesperado ao remover {name}: {str(e)}")


def add_client_cert(name):
    locations: list = list_client_certs()
    if name in locations:
        log(f"Cliente {name} já existe. Ignorando criação.")
        return

    client_dir: Path = CLIENTS_PATH / name
    client_dir.mkdir(parents=True, exist_ok=True)

    key_path = client_dir / "client.key"
    csr_path = client_dir / "client.csr"
    crt_path = client_dir / "client.crt"
    p12_path = client_dir / "client.p12"

    subj = f"/CN={name}/O=Clinica VidaMais/L=Palmital/ST=PR/C=BR"

    try:
        subprocess.run(["openssl", "genrsa", "-out", str(key_path), "4096"], check=True)
        log(CERTS_LOGPATH, f"Chave privada gerada para {name}: {key_path}")

        csr_resp = subprocess.run(
            [
                "openssl",
                "req",
                "-new",
                "-sha256",
                "-key",
                str(key_path),
                "-out",
                str(csr_path),
                "-subj",
                subj,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        log(
            CERTS_LOGPATH,
            f"CSR gerado para {name}: {csr_resp.stdout if csr_resp.stdout else 'Sucesso'}",
        )

        cert_resp = subprocess.run(
            [
                "openssl",
                "x509",
                "-req",
                "-sha256",
                "-days",
                "365",
                "-in",
                str(csr_path),
                "-CA",
                str(CA_PATH / "ca.crt"),
                "-CAkey",
                str(CA_PATH / "ca.key"),
                "-CAcreateserial",
                "-out",
                str(crt_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        log(
            CERTS_LOGPATH,
            f"Certificado assinado para {name}: {cert_resp.stdout if cert_resp.stdout else 'Sucesso'}",
        )

        p12_resp = subprocess.run(
            [
                "openssl",
                "pkcs12",
                "-export",
                "-out",
                str(p12_path),
                "-inkey",
                str(key_path),
                "-in",
                str(crt_path),
                "-certfile",
                str(CA_PATH / "ca.crt"),
                "-password",
                "pass:1234",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        log(CERTS_LOGPATH, f"Arquivo PKCS#12 gerado para {name}: {p12_path}")

        locations.append(name)
        with open(CLIENTS_JSON_PATH, "w") as f:
            json.dump({"clients": locations}, f)
        log(CERTS_LOGPATH, f"Cliente {name} adicionado com sucesso!")

        return True

    except subprocess.CalledProcessError as e:
        log(CERTS_LOGPATH, f"Erro ao gerar certificado para {name}: {e.stderr}")
    except Exception as e:
        log(CERTS_LOGPATH, f"Erro inesperado ao adicionar {name}: {str(e)}")


def get_client_p12_path(name):
    locations = list_client_certs()
    if name not in locations:
        abort(404, description="Cliente não encontrado")
    client_dir = Path(CLIENTS_PATH) / name

    return str(client_dir / "client.p12")
