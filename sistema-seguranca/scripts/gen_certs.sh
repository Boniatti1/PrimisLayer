CERTS_DIR="../data/nginx/certs"
mkdir -p "$CERTS_DIR"

# Gerar CA
openssl genrsa -out "$CERTS_DIR/ca.key" 4096
openssl req -new -x509 -sha256 -days 365 -key "$CERTS_DIR/ca.key" -out "$CERTS_DIR/ca.crt" \
  -subj "/CN=CA-VidaMais/O=Clinica VidaMais/L=Palmital/ST=PR/C=BR"

# Certificado do Servidor
openssl genrsa -out "$CERTS_DIR/server.key" 4096
openssl req -new -sha256 -key "$CERTS_DIR/server.key" -out "$CERTS_DIR/server.csr" \
  -subj "/CN=vidamais.top/O=Clinica VidaMais/L=Palmital/ST=PR/C=BR"
openssl x509 -req -sha256 -days 365 -in "$CERTS_DIR/server.csr" -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" -out "$CERTS_DIR/server.crt"

# Certificado do Cliente (mTLS)
openssl genrsa -out "$CERTS_DIR/client.key" 4096
openssl req -new -sha256 -key "$CERTS_DIR/client.key" -out "$CERTS_DIR/client.csr" \
  -subj "/CN=Computador Clinica 1/O=Clinica VidaMais/L=Palmital/ST=PR/C=BR"
openssl x509 -req -sha256 -days 365 -in "$CERTS_DIR/client.csr" -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" -out "$CERTS_DIR/client.crt"

# Pacote .p12
openssl pkcs12 -export -out "$CERTS_DIR/client.p12" -inkey "$CERTS_DIR/client.key" -in "$CERTS_DIR/client.crt" -certfile "$CERTS_DIR/ca.crt" -password pass:1234

chown -R $(logname):$(logname) "$CERTS_DIR"
chmod 600 "$CERTS_DIR"/*.key
chmod 644 "$CERTS_DIR"/*.crt "$CERTS_DIR"/*.csr "$CERTS_DIR"/*.p12