CA_DIR="../data/ssl"

# Criar estrutura de pastas
mkdir -p "$CA_DIR"/{ca,server,clients}
touch "$CA_DIR/ca/index.txt"
echo 1000 > "$CA_DIR/ca/serial"
echo 1000 > "$CA_DIR/ca/crlnumber"

# Gerar CA
openssl genrsa -out "$CA_DIR/ca/ca.key" 4096
chmod 600 "$CA_DIR/ca/ca.key"
openssl req -new -x509 -days 3650 -key "$CA_DIR/ca/ca.key" -out "$CA_DIR/ca/ca.crt" \
  -subj "/CN=CA-VidaMais/O=Clinica VidaMais/L=Palmital/ST=PR/C=BR"

# Certificado do Servidor
openssl genrsa -out "$CA_DIR/server/server.key" 4096
chmod 600 "$CA_DIR/server/server.key"
openssl req -new -key "$CA_DIR/server/server.key" -out "$CA_DIR/server/server.csr" \
  -subj "/CN=vidamais.top/O=Clinica VidaMais/L=Palmital/ST=PR/C=BR"
openssl x509 -req -days 365 -in "$CA_DIR/server/server.csr" \
  -CA "$CA_DIR/ca/ca.crt" -CAkey "$CA_DIR/ca/ca.key" -CAcreateserial \
  -out "$CA_DIR/server/server.crt"
rm "$CA_DIR/server/server.csr"

# Gerar CRL
openssl ca -gencrl -out "$CA_DIR/ca/crl.pem" \
  -keyfile "$CA_DIR/ca/ca.key" -cert "$CA_DIR/ca/ca.crt" \
  -config <(cat <<EOF
[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = $CA_DIR/ca
database          = \$dir/index.txt
certificate       = \$dir/ca.crt
private_key       = \$dir/ca.key
serial            = \$dir/serial
crlnumber         = \$dir/crlnumber
default_md        = sha256
policy            = policy_any

[ policy_any ]
countryName             = optional
stateOrProvinceName     = optional
organizationName        = optional
commonName              = supplied

[ crl_ext ]
authorityKeyIdentifier=keyid:always
EOF
)
