# Decisões

Sete registros de decisão de arquitetura do estudo, em forma condensada. Cada um mantém o formato usado no
repositório privado: contexto, decisão, alternativas consideradas, consequências. As datas são as datas dos
registros originais. Nenhuma dessas decisões foi exercitada em código em execução.

---

## ADR-0001 Monólito modular com contratos explícitos

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O produto é entregue a usuários finais em três sistemas operacionais e carrega quinze módulos
entre motor, runtimes, registro, memória, aprendizado, avaliação, políticas, agentes, API e interface. Ele
precisa instalar como uma coisa só, ser diagnosticável a partir de um log e crescer uma tarefa por vez sem
dependência de nuvem.

**Decisão.** Construir um produto instalável cujos módulos são separados por pacote e se comunicam apenas por
contratos de dados tipados validados em cada fronteira. Hardware, registro e runtime não sabem nada sobre a
interface ou sobre agentes. A API e a interface conhecem apenas a superfície pública do Motor de
Inteligência. Qualquer módulo pode ser substituído por uma implementação concorrente sem tocar nos outros,
desde que o contrato se sustente.

**Alternativas consideradas.** Microsserviços locais foram rejeitados porque operar e instalar uma malha de
serviços para um aplicativo desktop de usuário único compra latência e modos de falha parcial sem benefício.
Uma biblioteca única sem fronteiras internas se desenvolve rápido e depois acopla tudo, o que torna a troca
de um runtime impossível. Uma arquitetura de plugins com núcleo vazio foi rejeitada como flexibilidade
excessiva para um produto com escopo conhecido.

**Consequências.** As fronteiras precisam ser defendidas em testes, não em comentários de revisão:
importações de internos entre módulos reprovam o build. Cada tarefa do plano mapeia para um pacote, o produto
instala como uma unidade, e o motor continua utilizável sem a interface. A extração de um módulo para o próprio
processo segue possível ao custo de trabalho de empacotamento.

---

## ADR-0002 Camada de inferência universal com adaptadores de runtime

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O produto precisa rodar em AMD, NVIDIA, Intel, Apple e CPU pura, em Linux, Windows e macOS. Cada
runtime de inferência é forte em uma combinação diferente, e nenhum cobre todas elas com as mesmas garantias.
Amarrar a aplicação a um único runtime, ou a um único fornecedor, contradiz a razão de o produto existir.

**Decisão.** Definir um contrato de runtime cobrindo descoberta, instalação assistida, carga, descarga,
configuração de contexto, quantização e amostragem, geração com streaming e cancelamento, embedding, status,
métricas e diagnóstico. Implementar um adaptador por runtime: llama.cpp como principal, Ollama, vLLM e
Transformers como cobertura adicional, MLX como adaptador opcional em hardware Apple. As capacidades são
declaradas por método. Um adaptador que não consegue implementar um método com fidelidade declara a limitação;
simulá-la é falha de teste. A seleção de runtime pertence ao motor de roteamento, com o veredito de
compatibilidade como entrada, nunca ao chamador.

**Alternativas consideradas.** Apenas llama.cpp cobre muita coisa, mas deixa de fora a entrega de alto
throughput em GPUs dedicadas e o caminho de baixo atrito em que o Ollama já está instalado. Apenas Ollama
esconde os controles de memória, contexto e quantização que decidem a compatibilidade, e limita o hardware
àquilo que ele suporta. Uma abstração mínima de chat completions descartaria exatamente os controles que fazem
a diferença entre um modelo que roda e um que quebra.

**Consequências.** Todo adaptador precisa do próprio estado de validação por sistema operacional, backend e
dispositivo, e o custo de manutenção cresce com o número de adaptadores vivos. A lista inicial é, portanto,
curta. Um adaptador sem cobertura de teste real é desativado com uma nota de compatibilidade visível em vez de
mantido como suporte nominal.

---

## ADR-0003 O aprendizado nunca altera os pesos base

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O produto promete melhorar com o uso. A implementação direta, treinar o modelo base sobre a
atividade do usuário, é também a mais perigosa: esquecimento catastrófico, degradação silenciosa, envenenamento
por feedback, custo alto, nenhum rollback, e dados privados absorvidos em pesos que não podem ser auditados nem
apagados. Apagar logs não apaga o que os pesos retiveram.

**Decisão.** Nunca modificar os pesos base automaticamente. Dividir o aprendizado em duas camadas com
privilégios diferentes. O aprendizado rápido grava apenas artefatos reversíveis e legíveis por humanos:
preferências, instruções de contexto, memórias, procedimentos e configuração de roteamento, cada um com origem,
autor, versão e um caminho de desfazer. O aprendizado profundo produz adaptadores sobre uma base congelada,
treinados em ambiente isolado a partir de um dataset versionado e imutável, com avaliação pareada antes e
depois, um gate estatístico, promoção controlada, histórico de versões e rollback. Uma única interação nunca
causa mudança permanente, e a promoção automática é proibida por padrão.

**Alternativas consideradas.** O ajuste fino da base com dados de uso foi rejeitado pela perda de rollback,
pelo risco de esquecimento, pelo risco de contaminação e pela impossibilidade de honrar um pedido de exclusão.
Apenas prompt e contexto foi rejeitado porque descarta a especialização real por usuário, que é justamente o
que o gate existe para autorizar. Adotar um motor de aprendizado contínuo existente como dependência foi
rejeitado por maturidade e por suporte de hardware não validado; os conceitos foram reaproveitados, o código
não.

**Consequências.** Infraestrutura de avaliação e versionamento é necessária desde cedo, então o Motor de
Avaliação não é acessório. A interface precisa mostrar a versão de adaptador ativa, sua avaliação e um controle
de reversão. A melhoria é limitada pelo que os adaptadores conseguem entregar. A política é protegida por um
teste, porque se torna irreversível no momento em que alguém treina a base.

---

## ADR-0004 Consentimento como pré-condição para coleta, retenção e aprendizado

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** Os motores de memória e de experiência existem para registrar interações, e a interface mostra
métricas de memória e de aprendizado. Se isso se tornar captura automática de tudo, o produto contradiz a
própria promessa de privacidade. A pesquisa também constatou que várias bibliotecas prontas de memória para
agentes usam provedores remotos por padrão, o que é inaceitável como comportamento silencioso em um produto
local-first.

**Decisão.** Cinco regras. Local por padrão: nenhum dado deixa o host sem uma ação explícita, nomeada e
auditada, e uma dependência que faça egress por padrão não entra sem uma flag desativada e um aviso. Captura
seletiva: o registro exige consentimento por finalidade, ou seja, memória, avaliação ou treinamento, e o
consentimento é revogável com efeito sobre o uso futuro e uma revisão do uso passado. Retenção configurável:
expiração por tipo de memória, exportação em formato aberto e exclusão que alcança armazenamento primário,
índice de texto completo, índice vetorial, KV cache, pré-processamento, arquivos de write-ahead e de memória
compartilhada, exportações e backups. Rastreabilidade: toda memória e toda entrada de dataset mantém origem,
timestamp e justificativa de seleção, de modo que o sistema consiga responder por que sabe algo. Auditoria: o
acesso a dados pessoais é registrado e o usuário pode inspecionar, editar e apagar.

**Alternativas consideradas.** Capturar tudo e filtrar depois foi rejeitado porque contradiz a promessa, amplia
a superfície de exposição e transforma a exclusão em questão de sorte. Adotar um framework de memória como
dependência central foi rejeitado pelos padrões remotos, pelo modelo de retenção e pela exclusão não
executável; a taxonomia foi emprestada, não a propriedade dos dados. Um único prompt de consentimento na
instalação não cobre finalidades distintas nem sustenta revogação real.

**Consequências.** A exclusão se torna requisito testável em vários pontos, e o dataset de aprendizado precisa
de versionamento imutável. Isso dá mais trabalho do que armazenar tudo e decidir depois. Apertar é sempre
reversível; afrouxar não é, então qualquer relaxamento exige um novo registro e uma revisão de risco.

---

## ADR-0005 Pesquisa e arquitetura antes da implementação

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O plano de execução determina que funcionalidade não deve ser construída antes de a arquitetura
estar estabelecida. Escrever primeiro o código de runtime, de catálogo e de memória embutiria decisões de
fornecedor no núcleo, que é exatamente o desfecho que o projeto existe para evitar.

**Decisão.** A primeira fase foi executada como pesquisa verificável: catorze frentes independentes, cada uma
com um relatório no repositório privado, fontes abertas primárias em vez de trechos de busca, e um campo
obrigatório de verificação por afirmação, seja verificado, parcialmente verificado ou não verificado. Nenhuma
funcionalidade do produto foi implementada antes do encerramento dessa fase. Uma decisão técnica que altere um
contrato, o stack ou uma promessa de compatibilidade se torna um registro de decisão com evidência, e o
documento de contexto do projeto é atualizado na mesma entrega.

**Alternativas consideradas.** Prototipar imediatamente com um único runtime foi rejeitado porque o protótipo
se torna a arquitetura: escolhas de fornecedor, modelo de dados e API vazam para todo o código. Pesquisa
narrada sem artefatos foi rejeitada porque não pode ser refutada nem reaproveitada, e evidência versionada é o
que sustenta tanto as decisões quanto a revisão posterior.

**Consequências.** Várias correções chegaram antes de existir qualquer código: um modelo do catálogo inicial não
é executável localmente, a NPU não é uma rota geral de inferência, Vulkan precede ROCm na plataforma AMD alvo,
e o footprint de KV em contexto longo descarta configurações que o material do produto implicava. O custo é
tempo de calendário no início, compensado pelo retrabalho evitado. Pesquisa não é irreversível: nova evidência
pode substituir um registro, e o registro substituído permanece marcado como tal.

---

## ADR-0006 Compatibilidade declarada apenas com evidência de teste

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** Este mercado mistura afirmações de marketing com afirmações de engenharia. Frases como "roda um
modelo de 120B" ou "usa a NPU" muitas vezes não passam na aritmética de banda de memória e de tamanho de cache.
O produto roda em hardware que o usuário já possui, então uma afirmação de compatibilidade errada prejudica a
confiança no produto e na máquina.

**Decisão.** Compatibilidade é um estado verificado, nunca uma inferência a partir de um nome de fornecedor, de
uma contagem de parâmetros ou de um número nominal de TOPS. Seis estados são obrigatórios: testado, não
validado, compatível com limitações, incompatível, requer instalação, requer hardware adicional. Todo estado
carrega um registro de ambiente: sistema operacional e versão, kernel e driver, runtime e commit, backend,
dispositivo, carveout de memória quando aplicável, hash do artefato, quantização, contexto configurado,
concorrência testada, métricas medidas e data. Sem registro, o estado publicável mais alto é "não validado".
Números mostrados na interface vêm da medição do próprio aplicativo; um benchmark de terceiros pode aparecer
como referência identificada, nunca como expectativa do produto.

**Alternativas consideradas.** Uma matriz estática mantida à mão envelhece na velocidade dos drivers e esconde o
fato de que ninguém a testou. Rodar um smoke test e marcar a combinação como compatível ignora contexto longo,
concorrência e estabilidade, e justifica no máximo "não validado" ou "com limitações". Faixas genéricas como
"modelos grandes" são uma forma educada de não dizer nada enquanto empurram a decisão para o usuário.

**Consequências.** O produto precisa de instrumentação e de um pipeline de qualificação como trabalho permanente,
e haverá modelos que o aplicativo se recusa a oferecer em determinada máquina. Essa recusa é comportamento
correto e precisa aparecer como tal na interface. Endurecer essa política é barato; afrouxá-la exige tirar
informação do usuário.

---

## ADR-0007 Motor independente da interface

**Status:** aceito, com o shell desktop pendente de um protótipo medido. **Data:** 2026-11-21.

**Contexto.** O motor precisa continuar utilizável se a interface for substituída por outro aplicativo ou por um
cliente compatível, e o shell desktop é uma camada multiplataforma ainda a ser escolhida por medição. Se o motor
nascer dentro do processo da interface, essa substituição custa uma reescrita.

**Decisão.** Distribuir o motor como biblioteca importável e como serviço local, com a mesma superfície pública
em três caminhos: uma API interna tipada, uma ferramenta de linha de comando e um gateway compatível com OpenAI.
A interface desktop é um cliente que não detém estado canônico e não toma decisão de runtime. O shell inicial é
proposto como Tauri 2 com o motor Python como sidecar, condicionado a um protótipo que meça memória residente,
tamanho do instalador, comportamento de processo e custo do webview nos três sistemas operacionais. A escolha
final se torna um registro próprio quando esse protótipo existir. A superfície de rede escuta em loopback por
padrão, mantém o acesso cross-origin fechado, autentica mesmo localmente, armazena a chave como verificador e
exige uma ação explícita do usuário com aviso antes de qualquer alcance mais amplo.

**Alternativas consideradas.** Um motor embutido no processo da interface viola o requisito de que o núcleo
sobreviva a uma troca de interface e acopla os ciclos de release. Apenas HTTP, sem biblioteca, remove a tipagem e
torna o teste interno lento ao forçar serialização dentro de um processo. Escolher Electron sem medição pode até
estar certo, mas seria uma decisão tomada por hábito em vez de por dados.

**Consequências.** O contrato público é versionado, duas superfícies precisam ser testadas, e a linha de comando
tem de permanecer funcional como ferramenta de diagnóstico. Trocar o shell afeta apenas o diretório da aplicação,
que é o ponto da decisão.
