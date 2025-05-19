# Sistema de Segurança

Solução desenvolvida como parte do Programa Talento Tech na Disciplina 15 - Projeto Integrador.

## Desafio Proposto

Desenvolver um sistema automatizado para detecção e resposta a ameaças cibernéticas. A clínica sofreu uma tentativa de invasão recentemente. Ela usa um sistema simples de agendamento online, mas não monitora logs de acesso e nem implanta mecanismos para reportar e coibir invasões.

## Solução Desenvolvida

Foi criado um sistema de segurança baseado em proxy reverso que intercepta, analisa e responde a possíveis ameaças. A solução oferece:

- Monitoramento de Logs de acesso.
- Bloqueio automático de IPs suspeitos com fail2ban.
- Regras de segurança WAF com NAXSI.
- Proteção de rotas sensíveis via mTLS.
- Painel administrativo web com Flask.
- Alertas em tempo real via Telegram.
- Desenvolvimento em containers Docker, facilitando a implantação.

## Tecnologias Utilizadas

- **Docker**: Isolamento e portabilidade do ambiente.
- **NGINX**: Servidor web e proxy reverso.
- **NAXSI**: Firewall de aplicações web (WAF).
- **Fail2ban**: Detecção de comportamentos suspeitos e banimento de IPs.
- **Flask**: Aplicação web para o painel administrativo.
- **OpenSSL**: Emissão e revogação de certificados digitais.
- **Telegram Bot API**: Envio de alertas de segurança.

## Funcionalidades

- Proxy reverso para proteger o sistema da clínica.
- Painel administrativo para:
  - Gerenciar rotas protegidas.
  - Emitir e revogar certificados mTLS.
  - Visualizar eventos de segurança.
- Banimento automático de IPs com comportamento suspeito.
- Integração com Telegram para alertas em tempo real.
- Proteção por rota, com autenticação mTLS.

## Instalação

Em breve


