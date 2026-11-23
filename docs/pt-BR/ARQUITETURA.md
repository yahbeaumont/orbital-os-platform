# Arquitetura

A arquitetura estabelecida durante o estudo. Nada descrito aqui está implementado. As propostas dependem
de uma medição ainda não realizada, e os itens não verificados estão marcados como tal.

## 1. Contexto

ORBITAL OS é um aplicativo desktop, não um serviço e não um sistema operacional. O usuário o instala em
uma máquina, e essa máquina é a implantação inteira. Três consequências moldam todo o resto.

O núcleo é uma biblioteca com processo próprio. A interface é cliente do motor por meio de um contrato
interno, e o mesmo motor é alcançável como pacote importável, ferramenta de linha de comando e API HTTP
local. Um motor nascido dentro do processo da interface teria de ser reescrito sempre que a interface
mudasse.

O estado é local e canônico. Banco de dados, cache de modelos, logs, memória e trilha de auditoria vivem no
disco do usuário, de modo que backup é cópia de arquivo e exclusão é requisito do modelo de dados.

A instalação faz parte do produto. Um runtime ausente, uma instalação assistida, uma verificação de
integridade e um fallback para uma alternativa testada são caminhos normais, não tratamento excepcional de
erro.

## 2. Forma

Um monólito modular: um produto instalável, com módulos separados por pacote, comunicando-se apenas por
contratos tipados validados em cada fronteira. Sem microsserviços, sem fila distribuída, sem serviço
externo necessário para o produto funcionar. Seis camadas e uma regra de dependência:

```
Interface → Fronteira → Orquestração → Cognição → Execução → Fundação
```

Uma camada pode depender das camadas abaixo dela e nunca das que estão acima. A detecção de hardware, o
registro e a camada de runtime não sabem que uma interface existe, e o gateway de API conhece apenas a
superfície pública do Motor de Inteligência. Um teste de grafo de importações impõe a regra, de modo que uma
inversão reprova o build em vez de sobreviver a uma revisão.

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
| Motor de Políticas | Decisões de negar por padrão, aprovações, auditoria append-only |
| Runtime de Agentes | Run, Task, Tool, Approval, Event, Artifact, scheduler determinístico |
| Gateway de API | Subconjunto compatível com OpenAI declarado, streaming, autenticação local |
| Interface | Cliente do motor, sem estado canônico |

Quatro contratos sustentam o argumento.

O contrato de compatibilidade recebe uma especificação de modelo e um relatório de hardware e devolve um
veredito. A aritmética é explícita: pesos residentes a partir do total de parâmetros e dos bits efetivos por
peso, KV cache a partir de batch, contexto, número de camadas, cabeças de KV, dimensão de cabeça e tamanho
do elemento, depois espaço de rascunho, overhead de runtime e uma reserva de sistema. Metadados de camada e
de cabeça vêm do artefato, nunca de um arquétipo ilustrativo. Seis estados são obrigatórios: testado, não
validado, compatível com limitações, incompatível, requer instalação, requer hardware adicional.

O contrato de runtime cobre descoberta, instalação, carga, configuração, geração com streaming e
cancelamento, embedding, métricas e diagnóstico. As capacidades são declaradas por método, e uma limitação é
declarada em vez de simulada. A seleção de runtime pertence ao motor de roteamento.

O contrato de aprendizado separa trabalho reversível de trabalho irreversível. O aprendizado rápido grava
apenas artefatos inspecionáveis: preferências, instruções de contexto, memórias, procedimentos e
roteamento. O aprendizado profundo produz adaptadores sobre uma base congelada, em isolamento, a partir de um
dataset versionado e imutável, com avaliação antes e depois, um gate de promoção, histórico de versões e
rollback.

O contrato de políticas responde a toda pergunta sensível com negar por padrão, privilégio mínimo e herança
que não amplifica. As aprovações vinculam payload, recurso, ferramenta e validade, e a trilha de auditoria é
append-only e revogável.

## 4. Uma requisição

Uma requisição entra pela interface, pela linha de comando ou por um cliente compatível. O gateway pergunta
ao motor de políticas se a ação é permitida e com qual escopo. O Motor de Inteligência resolve intenção,
complexidade e um orçamento de contexto. O Motor de Memória devolve contexto consentido com a origem
anexada. O Motor de Roteamento seleciona um modelo, um runtime e uma cadeia de fallback, usando o veredito de
compatibilidade e o orçamento de memória como entradas. O adaptador carrega e configura o artefato e gera com
streaming enquanto reporta métricas. A resposta sai com seu registro de execução. O Motor de Experiência
registra a interação apenas onde existe consentimento, e o trabalho de aprendizado é enfileirado fora do
caminho da requisição.

A instalação segue o mesmo padrão: entrada de catálogo, avaliação de compatibilidade contra o artefato real,
orçamento de memória mostrado ao usuário, download oficial com checksum, registro, um teste funcional curto
e, então, o estado instalado ou o estado instalado com limitação, acompanhado de um diagnóstico legível.

## 5. Modelo de dados conceitual

Um relatório de hardware produz registros de dispositivo e de capacidade. Um registro de modelo aponta para
artefatos, cada um com um formato, uma quantização e um digest. Um registro de validação une um artefato, uma
versão de runtime, um backend e um dispositivo a uma descrição de ambiente e a um resultado. Vereditos de
compatibilidade são derivados de registros de validação e do relatório de hardware corrente, nunca
armazenados como afirmação autônoma. Uma conversa produz eventos; eventos selecionados sob consentimento se
tornam registros de memória, e registros referenciados por um dataset autorizado se tornam entradas de
dataset. Uma versão de dataset produz uma versão de adaptador, que aponta para uma revisão base, uma execução
de avaliação e uma decisão de promoção. Decisões de política e aprovações formam uma cadeia append-only que
referencia a ação autorizada por elas.

Toda afirmação de compatibilidade remete a um registro de ambiente, e todo artefato aprendido remete a um
dataset, uma revisão base e uma decisão de promoção.

## 6. Implantação

O motor é distribuído como wheel Python mais sidecars por plataforma. O shell desktop é proposto como Tauri 2
com o motor como processo sidecar, condicionado a um protótipo que meça memória, tamanho do instalador,
comportamento de processo e custo do webview nos três sistemas operacionais. O empacotamento começa com
PyInstaller e compara Nuitka. Os builds rodam em runners nativos por plataforma, porque compilação cruzada não
está disponível, e o atualizador verifica assinaturas. A integração contínua roda lint, tipos e testes em
Linux, Windows e macOS, e reporta testes dependentes de hardware como não executados em vez de omiti-los.

## 7. Limites conhecidos

Nada aqui foi executado. A fórmula de compatibilidade é fixa, mas não calibrada: os números de overhead são
uma reserva inicial até que instrumentação por backend os substitua. O índice vetorial está indefinido e será
escolhido por benchmark local, e o shell desktop é uma hipótese. A qualificação de hardware exige máquinas que
o ambiente de desenvolvimento não tem, então nenhum estado pode alcançar "testado" ainda. Números de
desempenho declarados por fabricante não foram reproduzidos, e a capacidade de memória de uma configuração não
pôde ser confirmada em fonte pública primária, razão pela qual o motor lê a capacidade em tempo de execução.
