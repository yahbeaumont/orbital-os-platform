# ORBITAL OS
[English](README.md) · **Português**

Um estudo de arquitetura para uma plataforma de IA local e agnóstica de hardware, entregue como aplicativo desktop.

![ORBITAL OS](docs/banner.png)

ORBITAL OS é um produto real em fase de arquitetura, construído para a linha de hardware ORBITAL e para
máquinas AMD, NVIDIA, Intel e CPU em geral. Este repositório é o registro público dessa fase: pesquisa,
arquitetura, registros de decisão e diagramas. Não contém código de produção e não reivindica nenhuma
compatibilidade de hardware que não tenha sido testada na máquina correspondente.

## Visão geral

ORBITAL OS é uma plataforma de IA local, modular e multiplataforma, distribuída como aplicativo para
Linux, Windows e macOS. Executa modelos no hardware do próprio usuário, com privacidade como configuração
padrão, e expõe um motor próprio com memória persistente, registro de experiência, aprendizado contínuo,
avaliação de qualidade, gerenciamento de modelos e, mais adiante, execução multiagente. Não é um sistema
operacional. É o aplicativo que roda na linha de hardware ORBITAL, cujas máquinas são construídas sobre
plataformas AMD Ryzen AI Max ([orbitalzerion.com](https://www.orbitalzerion.com/en/)), e é projetado para
rodar também no hardware de outros fabricantes. O mesmo núcleo precisa funcionar em AMD, NVIDIA, Intel e
CPU pura, em três sistemas operacionais, usando o runtime de inferência que melhor se ajuste à máquina à
frente do usuário.

O público deste estudo são engenheiros e revisores técnicos que querem ver como um produto de inferência
agnóstico de hardware é especificado antes de existir código: quais afirmações são demonstráveis, quais
são emprestadas de terceiros e quais permanecem não verificadas. Estado no encerramento da fase de
arquitetura: 57 arquivos, aproximadamente 4.000 linhas de documentação, 14 relatórios de pesquisa,
7 registros de decisão e 5 diagramas. Nenhum código de produção. Nenhuma compatibilidade declarada sem
teste de hardware.

## O problema

Um produto de inferência local precisa responder a três perguntas antes de executar qualquer coisa: qual
hardware está realmente presente, qual runtime consegue usar esse hardware e se um determinado modelo cabe
na memória. Cada pergunta tem uma resposta fácil de entregar e errada.

O hardware é descrito por folhas de marketing, não pelo sistema operacional. A página de um fabricante pode
listar um teto de memória enquanto a máquina na bancada reporta outro, e benchmarks públicos costumam ser
produzidos em uma configuração diferente da que está sendo vendida. Software que confia na folha de
especificações ou recusa modelos que teriam cabido ou aceita modelos que esgotam a memória no meio de uma
conversa. A mesma armadilha existe para aceleração: um nome de dispositivo não é uma capacidade, e um
número nominal de TOPS não diz nada sobre se um modelo em determinado formato consegue executar nessa
unidade.

Os runtimes são igualmente fragmentados. Nenhum runtime de inferência cobre AMD, NVIDIA, Intel, Apple e
CPU pura em Linux, Windows e macOS com as mesmas garantias, e cada um é forte em um canto diferente.
Comprometer o produto com um único runtime compromete o produto com o roadmap de um único fornecedor.

Por fim, o recurso que torna o produto interessante é o que tem mais chance de quebrar a confiança.
"Aprender com o seu uso" implementado como treinamento sobre o modelo base elimina a capacidade de
reverter, a capacidade de apagar e a capacidade de explicar por que o sistema mudou de comportamento.

## O que o produto faz

**Avaliar a máquina e o modelo.** A detecção de hardware inventaria o sistema operacional, a CPU, os
dispositivos gráficos, a memória e as bibliotecas de aceleração, e então executa um teste funcional curto
por API de aceleração em vez de confiar no nome do dispositivo. O motor de compatibilidade transforma esse
inventário em um orçamento de memória e em um de seis estados explícitos por modelo, de testado a
incompatível.

**Adquirir e executar modelos.** Um registro separa descoberta, instalação e execução, com proveniência
para cada campo de metadados. O gerenciador de modelos baixa de fontes oficiais com verificação de
checksum, e uma camada de runtime universal executa o artefato pelo adaptador que servir à máquina.

**Lembrar.** Um motor de memória mantém memórias episódicas, semânticas, procedurais e de preferência em um
armazenamento local com recuperação híbrida, rastreamento de origem, retenção configurável e exclusão que
alcança todo artefato derivado.

**Melhorar, com um gate.** O aprendizado rápido ajusta artefatos reversíveis, como preferências, instruções
de contexto, procedimentos e roteamento. O aprendizado profundo produz adaptadores versionados sobre um
modelo base congelado, avalia-os contra a versão corrente e só promove mediante melhoria demonstrada, com
rollback disponível a qualquer momento.

**Expor o motor.** O mesmo núcleo é utilizável como biblioteca importável, como ferramenta de linha de
comando e como API local com um subconjunto compatível com OpenAI declarado, de modo que clientes externos
e a interface desktop são ambos consumidores comuns.

**Agir por meio de agentes.** Um escopo posterior acrescenta um runtime de agentes com contratos próprios,
execução de ferramentas sob política e escolha de modelo por agente. Esta parte está especificada, não
construída.

## Arquitetura

![Architecture](diagrams/architecture.png)

Seis camadas, quinze módulos, uma regra de dependência: uma camada pode depender apenas das camadas abaixo
dela, e uma inversão reprova a suíte de testes em vez da revisão de código. Fonte: [diagrams/architecture.mmd](diagrams/architecture.mmd).

| Camada | Módulos | Responsabilidade |
| --- | --- | --- |
| Interface | Interface desktop | Apresenta o estado, coleta consentimento, nunca detém dados canônicos |
| Fronteira | Gateway de API, linha de comando | Subconjunto compatível com OpenAI declarado, streaming, autenticação local |
| Orquestração | Motor de Inteligência, Motor de Roteamento, Runtime de Agentes | Interpreta a requisição, escolhe modelo e runtime, executa agentes |
| Cognição | Motor de Memória, Motor de Experiência, Motor de Aprendizado, Motor de Avaliação | Recuperação, registro seletivo, adaptadores e seu gate, pontuação |
| Execução | Detecção de Hardware, Motor de Compatibilidade, Registro de Modelos, Gerenciador de Modelos, Runtime de Modelos | Inventário, vereditos, catálogo, artefatos, adaptadores |
| Fundação | Motor de Políticas, configuração, logging, armazenamento | Decisões de negar por padrão, trilha de auditoria, persistência local |

Uma requisição chega à fronteira, é verificada pelo motor de políticas e alcança o Motor de Inteligência,
que resolve intenção, complexidade e um orçamento de contexto. O Motor de Memória devolve contexto
consentido com a origem anexada. O Motor de Roteamento escolhe um modelo, um runtime e uma cadeia de
fallback, usando um veredito de compatibilidade como entrada. O adaptador de runtime carrega o artefato,
gera com streaming e reporta métricas. A resposta sai pela fronteira com seu registro de execução, enquanto
o Motor de Experiência registra a interação apenas se houver consentimento, e a fila de aprendizado
permanece fora do caminho da requisição. A sequência está desenhada em [diagrams/flow.mmd](diagrams/flow.mmd).

## Destaques de engenharia

### Dimensionar modelos a partir da memória que o runtime reporta

O problema: documentação de fabricante, artigos de benchmark e a máquina à frente do usuário discordam
sobre quanta memória existe, e um modelo aceito no papel pode esgotar a memória durante a geração. A
decisão: o motor de compatibilidade dimensiona cada candidato contra a memória que o sistema operacional
reporta em tempo de execução, mais o resultado de um teste funcional por API de aceleração, nunca contra
uma especificação nominal. O orçamento é explícito: pesos residentes a partir do total de parâmetros e dos
bits efetivos por peso, um KV cache a partir dos metadados de camada e de cabeça do próprio artefato,
espaço de rascunho e uma reserva de 20 a 25 por cento da memória para o sistema, com 10 a 15 por cento do
orçamento de inferência para overhead. O veredito é um de seis estados, e apenas um teste de ambiente
registrado pode produzir "testado". O trade-off: o software permanece correto em hardware que ninguém
qualificou, o que também significa responder "compatível, não validado" onde uma página de marketing
preferiria "suportado". O produto não pode prometer que um modelo roda em uma máquina que não viu, porque a
resposta honesta depende da memória reportada por aquela unidade.

### Um núcleo, vários runtimes, com capacidades declaradas

O problema: nenhum runtime cobre AMD, NVIDIA, Intel, Apple e CPU em três sistemas operacionais, e envolver
a aplicação em torno de um deles importa os limites daquele fornecedor para dentro do produto. A decisão:
um contrato de runtime com descoberta, instalação, carga, configuração, geração, embedding, status, métricas
e diagnóstico, implementado uma vez por adaptador para llama.cpp, Ollama, vLLM, Transformers e,
opcionalmente, MLX. As capacidades são declaradas por método. Um adaptador que não consegue implementar um
método declara a limitação com honestidade e a chamada falha de forma ruidosa; simular o comportamento é
tratado como falha de teste. A seleção pertence ao motor de roteamento, com o veredito de compatibilidade
como entrada, nunca ao chamador. O trade-off: cada adaptador carrega a própria matriz de validação por
sistema operacional, backend e dispositivo, de modo que o custo de manutenção cresce com o número de
adaptadores mantidos vivos. Uma lista curta de adaptadores bem testados vale mais do que cobertura nominal
ampla, e um adaptador que ninguém testa é desativado em vez de remendado dentro do contrato.

### Aprendizado que não pode corromper o modelo base

O problema: "aprende com você" implementado como treinamento sobre o modelo base destrói rollback, exclusão
e auditabilidade, e degrada em silêncio. A decisão: duas camadas com privilégios diferentes. O aprendizado
rápido grava apenas artefatos reversíveis e legíveis por humanos: preferências, instruções de contexto,
memórias, procedimentos e configuração de roteamento. O aprendizado profundo produz adaptadores LoRA, QLoRA
ou DoRA sobre uma base congelada, treinados em isolamento a partir de um dataset versionado e imutável,
pontuados antes e depois com comparação pareada, e promovidos apenas quando a melhoria é demonstrada. Todo
adaptador tem linhagem, histórico de versões, um ponteiro corrente e um anterior, e rollback. A promoção
automática é proibida por padrão. O trade-off: a melhoria alcançável é limitada pelo que os adaptadores
entregam, e o Motor de Avaliação passa a ser pré-requisito em vez de acessório. Uma única interação nunca
pode causar uma mudança permanente, o que torna o produto mais lento para se adaptar do que a promessa
sugere. A exclusão também precisa alcançar adaptadores derivados, não apenas o texto armazenado.

### Negar por padrão para a autonomia local

O problema: agentes e ferramentas rodam com as credenciais do próprio usuário na máquina do próprio
usuário, então um padrão permissivo é uma escalada de privilégio local esperando por uma descrição de
ferramenta ruim. A decisão: o motor de políticas fica na camada de fundação e toda ação sensível o
consulta. O padrão é negar, o privilégio é mínimo, a herança nunca amplifica, as aprovações vinculam
payload, recurso, ferramenta e validade, e a trilha de auditoria é append-only, com revogação. O isolamento
usa o que cada sistema operacional realmente oferece, seccomp com Landlock, AppContainer com job objects ou
App Sandbox, e falha fechado com uma mensagem visível quando a plataforma não consegue entregar a proteção
solicitada. MCP é uma fronteira de interoperabilidade, não uma autoridade de confiança. O trade-off: mais
solicitações de aprovação, recursos indisponíveis em plataformas sem a primitiva de isolamento e uma
obrigação de interface de declarar qual proteção foi realmente aplicada em vez de qual era a pretendida.

## Stack tecnológico

| Camada | Escolha | Por quê |
| --- | --- | --- |
| Linguagem do núcleo | Python 3.12 com uv | O único ecossistema em que llama.cpp, Ollama, vLLM, Transformers e PEFT têm integrações funcionais |
| Contratos | pydantic v2, esquemas versionados | Um tipo validado em cada borda de módulo elimina uma classe de erro de integração |
| Persistência | SQLite em modo WAL com FTS5 | Zero operações, transacional, backup em nível de arquivo, exclusão auditável |
| Índice vetorial | Plugável atrás de uma interface interna | sqlite-vec, LanceDB embarcado e busca exata são comparados por benchmark local, não por reputação |
| Runtime principal | llama.cpp, release estável fixada, Vulkan primeiro | Cobre CPU, CUDA, HIP, Vulkan e Metal com uma família de binários e artefatos GGUF |
| Runtimes adicionais | Ollama, vLLM, Transformers, MLX apenas em Apple | Cada um cobre um perfil que o runtime principal atende mal |
| Aprendizado | PEFT e TRL para LoRA, QLoRA e DoRA | Caminho documentado do treinamento de adaptador até um adaptador GGUF servível |
| API local | FastAPI com um subconjunto OpenAI declarado | Clientes externos funcionam sem camada de tradução, streaming incluído |
| Isolamento | seccomp e Landlock, AppContainer, App Sandbox | Primitivas nativas por plataforma, com capacidades declaradas e comportamento de falha fechada |
| Shell desktop | Tauri 2 com o motor como sidecar, proposto | Condicionado a um protótipo medido nos três sistemas operacionais, não adotado por reputação |
| Distribuição | Wheel do motor mais sidecars por sistema operacional, matriz de CI nativa, atualizador assinado | PyInstaller não é um compilador cruzado, então cada plataforma compila no próprio runner |

## Em números

| Métrica | Valor |
| --- | --- |
| Arquivos no repositório no encerramento da fase de arquitetura | 57 |
| Linhas de documentação | aproximadamente 4.000 |
| Relatórios de pesquisa com fontes primárias | 14 |
| Registros de decisão de arquitetura | 7 |
| Diagramas, fonte Mermaid mais PNG renderizado | 5 |
| Commits | 5 |
| Scripts Python auxiliares (calculadora de memória, gate de entrega) | 2 |
| Código de produção | 0 |

As contagens descrevem o repositório de trabalho privado ao final da fase de arquitetura. Este repositório
público publica dois dos cinco diagramas, os registros de decisão em forma condensada e três exemplos
escritos para publicação. As contagens estão incluídas porque são verificáveis, não porque volume seja uma
virtude: a saída útil daquela fase é o conjunto de decisões, e várias delas são correções.

## Segurança e privacidade

O que o design especifica: um motor de políticas com negar por padrão, privilégio mínimo e herança que não
amplifica; isolamento de capacidades por sistema operacional com uma declaração explícita do que foi
aplicado; consentimento por finalidade para captura de memória, avaliação e treinamento, revogável com
efeito sobre o uso novo; auditoria append-only de ações sensíveis com revogação; uma fronteira de dados
local em que nada deixa o host sem uma ação nomeada, explícita e auditada; uma API local vinculada ao
loopback com autenticação mesmo na mesma máquina, chaves armazenadas como verificadores em vez de texto
puro, e nenhum segredo anunciado na descoberta de rede.

O que explicitamente não está garantido nesta fase: nada do acima está implementado, então nada disso pode
ser usado como base de confiança. Não há software em execução para atacar nem postura de segurança para
testar. O isolamento depende da versão e da configuração do sistema operacional realmente presentes, e o
design exige que o produto reporte um nível de proteção reduzido em vez de aceitá-lo em silêncio.
Dependências de terceiros, licenças de modelos e termos de redistribuição de runtimes são revisados item a
item e não estão cobertos por nenhuma declaração genérica aqui.

## Escopo deste repositório

Publicado: as conclusões da pesquisa com suas fontes, a arquitetura e seus contratos, os sete registros de
decisão em forma condensada, o modelo de segurança, os dois diagramas que sustentam o argumento e três
exemplos pequenos que demonstram técnica.

Deliberadamente omitido: o corpus de pesquisa do próprio produto na íntegra, os termos comerciais de
hardware, as alegações de desempenho do cliente como qualquer coisa que não declarações de terceiros
atribuídas, identificadores internos e detalhes de infraestrutura, o material de referência visual
fornecido pelo cliente e qualquer implementação. Não há implementação a omitir: a fase de arquitetura
produziu documentos, não software. Os exemplos deste repositório foram escritos do zero para publicação e
não compartilham código com o trabalho privado.

## Mapa do repositório

```
orbital-os/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── banner.png           banner do repositório
│   ├── ARCHITECTURE.md      camadas, contratos, fluxo da requisição, modelo de dados, limites
│   ├── DECISIONS.md         sete registros de decisão
│   ├── CASE-STUDY.md        projetando a estratégia de runtime antes de escrever código
│   └── SECURITY.md          ativos, fronteiras, ameaças, controles, lacunas
├── diagrams/
│   ├── architecture.mmd     seis camadas e a regra de dependência
│   ├── architecture.png
│   ├── flow.mmd             uma requisição por roteamento, runtime, memória, avaliação
│   └── flow.png
└── examples/
    ├── README.md
    ├── runtime_contract.py  contrato de adaptador com capacidades declaradas
    ├── memory_fit.py        ajuste do modelo contra a memória reportada
    └── adapter_gate.py      máquina de estados de promoção e rollback
```

## Documentação

- [Arquitetura](docs/pt-BR/ARQUITETURA.md)
- [Decisões](docs/pt-BR/DECISOES.md)
- [Estudo de caso](docs/pt-BR/ESTUDO-DE-CASO.md)
- [Segurança e privacidade](docs/pt-BR/SEGURANCA.md)
- [English](README.md)

## Autor

Hay Beaumont, engenheiro de software, [github.com/yahbeaumont](https://github.com/yahbeaumont).
