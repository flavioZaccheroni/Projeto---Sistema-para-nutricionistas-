# Implementação da auditoria — 15/08/2026

Este documento rastreia as pendências P01–P15 da planilha de auditoria para a
implementação realizada no repositório. “Externo” identifica aceite ou infraestrutura
que não pode ser fabricado pelo código.

| ID | Resultado implementado | Estado verificável |
|---|---|---|
| P01 | `.venv` recriada e executável no projeto em `D:`; comandos atualizados. | Implementado |
| P02 | Troca obrigatória no primeiro acesso, senha forte, bloqueio temporário e auditoria. | Implementado |
| P03 | Consentimento versionado, exportação de dados, retenção e anonimização controlada. | Implementado; política/base legal requer revisão jurídica externa |
| P04 | Cadastro versionado de regras, fontes, revisor e CRN; release bloqueado até aprovação. | Fluxo implementado; aprovações profissionais são externas |
| P05 | Backup criptografado, restauração com integridade, retenção e execução automática configurável. | Implementado; destino/segredo devem ser configurados pela clínica |
| P06 | CI Windows, Ruff, cobertura mínima, teste Qt de fumaça e instalador. | Implementado; aceite em máquina limpa é externo |
| P07 | Gráfico longitudinal com filtros por paciente e indicador. | Implementado |
| P08 | Portal responsivo autenticado, publicações e registro de adesão por API local. | Implementado localmente; notificações e recuperação remota dependem de hospedagem |
| P09 | Conteúdo dinâmico por API e sessão no servidor local. | Implementado localmente; domínio/TLS/hospedagem são externos |
| P10 | HTTP/file sync real, Bearer, segredo em ambiente, idempotência, retries e erros. | Implementado; conectores homologados dependem do provedor |
| P11 | Estratégia híbrida: regras locais padrão e modelo externo opcional com consentimento e minimização. | Implementado; credenciais/avaliação do modelo escolhido são externas |
| P12 | PDF A4 com identidade, CRN, área de assinatura e testes. | Implementado; assinatura digital requer certificado externo |
| P13 | Decisão arquitetural documentada: SQLite offline até surgir requisito multiusuário. | Concluído conforme critério condicional da auditoria |
| P14 | Importação CSV TACO/TBCA/regional com versão, licença, validação e procedência. | Implementado; arquivo/licença oficial devem ser fornecidos pelo titular |
| P15 | Documentação UTF-8, script Inno Setup e notas de build/release. | Implementado; assinatura e validação final dependem de certificado/máquina externa |

## Backup automático

Ative `backup_automatico_ativo=1` na configuração e defina no ambiente do processo:

```powershell
$env:NUTRI_BACKUP_DIR = 'E:\Backup-Nutri-Clinic-Pro'
$env:NUTRI_BACKUP_PASSPHRASE = '<senha forte com 12 ou mais caracteres>'
```

O app verifica o intervalo na inicialização, cria somente `.ncpbackup` criptografado,
aplica a retenção configurada e registra o evento na auditoria. A senha não é salva no
banco clínico.

## Bloqueios de produção preservados

O checklist de implantação deve permanecer reprovado enquanto existirem referências
clínicas sem aprovação profissional ou não houver evidência de backup criptografado.
Isso impede que uma entrega técnica seja confundida com validação clínica, jurídica ou
operacional.
