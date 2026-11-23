# Arquitetura

A arquitetura que ficou do estudo. Nada do que está descrito aqui foi implementado. As propostas dependem de
uma medição que ainda não foi feita, e os itens não verificados aparecem marcados como tal.

## 1. Contexto

ORBITAL OS é aplicativo desktop, não serviço e não sistema operacional. O usuário instala em uma máquina, e
essa máquina é a implantação inteira. Três consequências organizam todo o resto.

O núcleo é uma biblioteca com processo próprio. A interface é cliente do motor por um contrato interno, e o
mesmo motor se alcança como pacote importável, ferramenta de linha de comando e API HTTP local. Motor nascido
dentro do processo da interface teria de ser reescrito a cada mudança de interface.

O estado é local e canônico. Banco, cache de modelos, logs, memória e trilha de auditoria ficam no disco do
usuário: backup vira cópia de arquivo, e exclusão vira requisito do modelo de dados.

A instalação faz parte do produto. Runtime ausente, instalação assistida, verificação de integridade e
fallback para uma alternativa testada são caminho normal, não tratamento de exceção.

## 2. Forma

Monólito modular: um produto instalável, com módulos separados por pacote que conversam apenas por contratos
tipados, validados em cada fronteira. Sem microsserviço, sem fila distribuída, sem serviço externo
obrigatório para o produto funcionar. Seis camadas e uma regra de dependência:

```
Interface → Fronteira → Orquestração → Cognição → Execução → Fundação
```

Uma camada pode depender das que estão abaixo e nunca das que estão acima. Detecção de hardware, registro e
camada de runtime não sabem que existe uma interface, e o gateway de API conhece apenas a superfície pública
do Motor de Inteligência. Um teste de grafo de importação sustenta a regra: inversão reprova o build em vez
de sobreviver à revisão.

| Camada | Módulos |
| --- | --- |
| Interface | Interface desktop |
| Fronteira | Gateway de API, linha de comando |
| Orquestração | Motor de Inteligência, Motor de Roteamento, Runtime de Agentes |
| Cognição | Memória, Experiência, Aprendizado, Avaliação |
| Execução | Detecção de Hardware, Motor de Compatibilidade, Registro de Modelos, Gerenciador de Modelos, Runtime de Modelos |
| Fundação | Motor de Políticas, configuração, logging estruturado, caminhos, armazenamento local |

## 3. Responsabilidades e contratos

| Módulo | Responsabilidade |
| --- | --- |
| Detecção de Hardware | Inventário em camadas mais um teste funcional por API de aceleração |
| Motor de Compatibilidade | Orçamento de memória e um veredito de seis estados por modelo e máquina |
| Registro de Modelos | Catálogo com proveniência, separando descoberta, instalação e execução |
| Gerenciador de Modelos | Download oficial, checksum, cache deduplicado, remoção segura |
| Runtime de Modelos | Contrato de adaptador sobre llama.cpp, Ollama, vLLM, Transformers e MLX opcional |
| Motor de Inteligência | Interpretação da requisição, orquestração, resposta padronizada |
| Motor de Roteamento | Escolha de modelo e runtime a partir de intenção, custo, orçamento e histórico |
| Motor de Memória | Quatro tipos de memória, recuperação híbrida, retenção, exclusão completa |
| Motor de Experiência | Registro seletivo e consentido de interações |
| Motor de Aprendizado | Camada rápida reversível e camada de adaptadores com gate |
| Motor de Avaliação | Conjuntos de avaliação, comparação pareada, detecção de regressão |
| Motor de Políticas | Decisão de negar por padrão, aprovações, auditoria append-only |
| Runtime de Agentes | Run, Task, Tool, Approval, Event, Artifact, scheduler determinístico |
| Gateway de API | Subconjunto compatível com OpenAI declarado, streaming, autenticação local |
| Interface | Cliente do motor, sem estado canônico |

Quatro contratos sustentam o argumento.

O contrato de compatibilidade recebe uma especificação de modelo e um relatório de hardware, e devolve um
veredito. A aritmética é explícita: pesos residentes a partir do total de parâmetros e dos bits efetivos por
peso; KV cache a partir de batch, contexto, número de camadas, cabeças de KV, dimensão de cabeça e tamanho do
elemento; depois espaço de scratch, overhead de runtime e reserva para o sistema. Metadados de camada e de
cabeça vêm do artefato, nunca de um arquétipo ilustrativo. Seis estados são obrigatórios: testado, não
validado, compatível com limitações, incompatível, requer instalação, requer hardware adicional.

O contrato de runtime cobre descoberta, instalação, carga, configuração, geração com streaming e
cancelamento, embedding, métricas e diagnóstico. Cada método declara suas capacidades, e limitação se
declara, não se simula. Escolher runtime é tarefa do motor de roteamento.

O contrato de aprendizado separa trabalho reversível de irreversível. O aprendizado rápido grava apenas
artefatos inspecionáveis: preferências, instruções de contexto, memórias, procedimentos e roteamento. O
aprendizado profundo produz adaptadores sobre base congelada, em isolamento, a partir de dataset versionado e
imutável, com avaliação antes e depois, gate de promoção, histórico de versões e rollback.

O contrato de políticas responde a toda pergunta sensível com negar por padrão, privilégio mínimo e herança
que não amplifica. As aprovações vinculam payload, recurso, ferramenta e validade, e a trilha de auditoria é
append-only e revogável.

## 4. Uma requisição

A requisição entra pela interface, pela linha de comando ou por um cliente compatível. O gateway pergunta ao
motor de políticas se a ação é permitida e com que escopo. O Motor de Inteligência resolve intenção,
complexidade e orçamento de contexto. O Motor de Memória devolve contexto consentido, com origem anexada. O
Motor de Roteamento escolhe modelo, runtime e cadeia de fallback, e toma como entrada o veredito de
compatibilidade e o orçamento de memória. O adaptador carrega e configura o artefato, gera com streaming e
reporta métricas. A resposta sai com o registro de execução. O Motor de Experiência registra a interação só
onde há consentimento, e o trabalho de aprendizado entra numa fila fora do caminho da requisição.

A instalação segue o mesmo padrão: entrada de catálogo, avaliação de compatibilidade contra o artefato real,
orçamento de memória mostrado ao usuário, download oficial com checksum, registro, teste funcional curto e,
no fim, estado instalado ou estado instalado com limitação, acompanhado de diagnóstico legível.

## 5. Modelo de dados conceitual

Um relatório de hardware produz registros de dispositivo e de capacidade. Um registro de modelo aponta para
artefatos, cada um com formato, quantização e digest. Um registro de validação amarra um artefato, uma versão
de runtime, um backend e um dispositivo a uma descrição de ambiente e a um resultado. Vereditos de
compatibilidade derivam de registros de validação e do relatório de hardware corrente; nunca ficam guardados
como afirmação solta. Uma conversa produz eventos; eventos escolhidos sob consentimento viram registros de
memória, e registros usados por um dataset autorizado viram entradas de dataset. Uma versão de dataset produz
uma versão de adaptador, que aponta para uma revisão base, uma execução de avaliação e uma decisão de
promoção. Decisões de política e aprovações formam uma cadeia append-only que referencia a ação autorizada.

Toda afirmação de compatibilidade remonta a um registro de ambiente, e todo artefato aprendido remonta a um
dataset, a uma revisão base e a uma decisão de promoção.

## 6. Implantação

O motor sai como wheel Python mais sidecars por plataforma. O shell desktop está proposto como Tauri 2, com o
motor em processo sidecar, e a escolha depende de um protótipo que meça memória, tamanho do instalador,
comportamento de processo e custo do webview nos três sistemas operacionais. O empacotamento começa com
PyInstaller e compara Nuitka. Como não há compilação cruzada, cada plataforma compila no próprio runner, e o
atualizador verifica assinaturas. A integração contínua roda lint, tipagem e testes em Linux, Windows e macOS,
e reporta teste dependente de hardware como não executado, em vez de omitir.

## 7. Limites conhecidos

Nada aqui foi executado. A fórmula de compatibilidade é fixa, mas não calibrada: os números de overhead são
reserva inicial até que instrumentação por backend os substitua. O índice vetorial segue indefinido e será
escolhido por benchmark local. O shell desktop é hipótese. Qualificação de hardware exige máquinas que o
ambiente de desenvolvimento não tem, então nenhum estado chega a "testado" por enquanto. Números de
desempenho declarados por fabricante não foram reproduzidos, e a capacidade de memória de uma configuração
não pôde ser confirmada em fonte pública primária. É por isso que o motor lê a capacidade em tempo de
execução.
