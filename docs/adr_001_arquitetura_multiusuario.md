# ADR 001 — Arquitetura desktop e evolução multiusuário

## Decisão

A versão 1.x permanece desktop, offline-first e com SQLite por instalação. Não há
requisito confirmado de edição concorrente entre clínicas ou unidades; introduzir
PostgreSQL e uma API agora aumentaria superfície de ataque e operação sem um caso de
uso aprovado.

## Gatilhos para evolução

Adotar API autenticada e PostgreSQL quando existir ao menos um destes requisitos:

- edição simultânea do mesmo prontuário por mais de um dispositivo;
- operação multiunidade com base central;
- portal hospedado com sincronização pela internet;
- integrações que exijam webhooks públicos e processamento assíncrono.

Antes da migração deverão ser definidos isolamento por clínica, autorização por
registro, TLS, gestão de segredos, trilha de auditoria, estratégia offline e plano de
migração/reversão. O servidor local do paciente é um canal de demonstração em
`127.0.0.1`; não substitui uma implantação HTTPS.
