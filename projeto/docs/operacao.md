# Operação da demonstração

O deployment disponível é local. No terminal de projeto executar python -m uvicorn api:app --host 127.0.0.1 --port 8000 e abrir http://127.0.0.1:8000. GET /health identifica o modelo e a aprovação offline; GET /schema lista as colunas; POST /predict aceita de 1 a 1000 fluxos; /docs mostra o contrato interativo. A API não recebe ficheiros de modelos nem permite modificar o limiar. A CLI admite um limiar explícito para exploração.

O artefacto deve ser carregado apenas a partir deste projeto e com a versão sklearn registada. Usar requirements-lock.txt para reproduzir o ambiente. models/schema.json e reports/avaliacao_final.json permitem verificar esquema, hash dos dados e decisão original de deployment.

A imagem Docker serve a mesma API. O Dockerfile é fornecido, mas a execução de Docker depende de Docker instalado. Não há autenticação nem TLS na demonstração local; uma implantação externa exigiria esses componentes e avaliação operacional.

Monitorização proposta: rever alertas e latência semanalmente; avaliar recall, precisão e FPR em fluxos com rótulos confirmados; rever drift mensalmente. PSI acima de 0,25 é um sinal para investigação, não uma garantia de falha ou uma instrução de retreino. A demonstração compara o primeiro e último dia e mistura alteração da classe e contexto temporal.

Para uma versão nova, recolher amostras recentes com as duas classes, definir entidades independentes e uma nova reserva de teste antes de experimentar. O teste atual já foi observado e não pode ser reutilizado repetidamente para escolher melhorias e continuar a ser apresentado como inédito.

Rollback: selecionar um commit anterior e o respetivo conjunto de dependências e modelos num checkout separado. Não sobrescrever modelos históricos sem preservar o manifesto e a avaliação. O projeto nunca executa bloqueio na firewall.
