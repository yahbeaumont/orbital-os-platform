# Decisões

Sete registros de decisão de arquitetura do estudo, em forma condensada. Cada um mantém o formato do
repositório privado: contexto, decisão, alternativas consideradas, consequências. As datas são as dos
registros originais. Nenhuma dessas decisões foi exercitada em código em execução.

---

## ADR-0001 Monólito modular com contratos explícitos

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O produto chega a usuários finais em três sistemas operacionais e carrega quinze módulos entre
motor, runtimes, registro, memória, aprendizado, avaliação, políticas, agentes, API e interface. Precisa
instalar como uma coisa só, ser diagnosticável a partir de um log e crescer uma tarefa por vez, sem
dependência de nuvem.

**Decisão.** Construir um produto instalável, com módulos separados por pacote que conversam apenas por contratos de
dados tipados, validados em cada fronteira. Hardware, registro e runtime não sabem que existem interface ou
agentes. A API e a interface conhecem só a superfície pública do Motor de Inteligência. Qualquer módulo pode
ser trocado por uma implementação concorrente sem tocar nos outros, desde que o contrato se sustente.

**Alternativas consideradas.** Microsserviços locais foram rejeitados: operar e instalar uma malha de
serviços para um aplicativo desktop de usuário único compra latência e modos de falha parcial sem nenhum
benefício. Uma biblioteca única, sem fronteiras internas, desenvolve rápido e depois acopla tudo, o que torna
a troca de runtime impossível. Arquitetura de plugins com núcleo vazio foi rejeitada como flexibilidade
excessiva para um produto de escopo conhecido.

**Consequências.** As fronteiras se defendem em teste, não em comentário de revisão: importação de interno
entre módulos reprova o build. Cada tarefa do plano mapeia para um pacote, o produto instala como unidade
única, e o motor continua utilizável sem a interface. Extrair um módulo para o próprio processo segue
possível, ao custo de trabalho de empacotamento.

---

## ADR-0002 Camada de inferência universal com adaptadores de runtime

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O produto precisa rodar em AMD, NVIDIA, Intel, Apple e CPU pura, em Linux, Windows e macOS. Cada
runtime de inferência é forte em uma combinação diferente, e nenhum cobre todas com as mesmas garantias.
Amarrar a aplicação a um runtime, ou a um fornecedor, contradiz a razão de o produto existir.

**Decisão.** Definir um contrato de runtime que cobre descoberta, instalação assistida, carga, descarga, configuração
de contexto, quantização e amostragem, geração com streaming e cancelamento, embedding, status, métricas e
diagnóstico. Um adaptador por runtime: llama.cpp como principal, Ollama, vLLM e Transformers como cobertura
adicional, MLX como adaptador opcional em hardware Apple. Cada método declara suas capacidades. Adaptador que
não implementa um método com fidelidade declara a limitação; simular é falha de teste. Escolher runtime cabe
ao motor de roteamento, com o veredito de compatibilidade como entrada, nunca ao chamador.

**Alternativas consideradas.** llama.cpp sozinho cobre muita coisa, mas deixa de fora a entrega de alto
throughput em GPU dedicada e o caminho de baixo atrito de quem já tem Ollama instalado. Ollama sozinho esconde
os controles de memória, contexto e quantização que decidem compatibilidade, e limita o hardware à lista que
ele cobre. Uma abstração mínima de chat completions descartaria exatamente os controles que separam um modelo
que roda de um que quebra.

**Consequências.** Todo adaptador precisa do próprio estado de validação por sistema operacional, backend e
dispositivo, e o custo de manutenção cresce com o número de adaptadores vivos. Por isso a lista inicial é
curta. Adaptador sem cobertura de teste real é desativado com nota de compatibilidade visível, não mantido
como suporte nominal.

---

## ADR-0003 O aprendizado nunca altera os pesos base

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O produto promete melhorar com o uso. A implementação direta, treinar o modelo base sobre a
atividade do usuário, é também a mais perigosa: esquecimento catastrófico, degradação silenciosa,
envenenamento por feedback, custo alto, nenhum rollback e dados privados absorvidos em pesos que não dá para
auditar nem apagar. Apagar os logs não apaga o que os pesos retiveram.

**Decisão.** Nunca alterar os pesos base automaticamente. O aprendizado se divide em duas camadas, com
privilégios diferentes. A rápida grava apenas artefatos reversíveis e legíveis por humanos: preferências,
instruções de contexto, memórias, procedimentos e configuração de roteamento, cada um com origem, autor,
versão e caminho de desfazer. A profunda produz adaptadores sobre base congelada, treinados em ambiente
isolado a partir de dataset versionado e imutável, com avaliação pareada antes e depois, gate estatístico,
promoção controlada, histórico de versões e rollback. Uma interação nunca causa mudança permanente, e
promoção automática é proibida por padrão.

**Alternativas consideradas.** Ajuste fino da base com dados de uso foi rejeitado pela perda de rollback,
pelo risco de esquecimento, pelo risco de contaminação e pela impossibilidade de honrar um pedido de exclusão.
Só prompt e contexto foi rejeitado porque descarta a especialização real por usuário, que é justamente o que o
gate autoriza. Adotar um motor de aprendizado contínuo de terceiros como dependência foi rejeitado por
maturidade e por suporte de hardware não validado: os conceitos foram reaproveitados, o código não.

**Consequências.** Infraestrutura de avaliação e versionamento passa a ser necessária desde cedo, então o
Motor de Avaliação não é acessório. A interface precisa mostrar a versão de adaptador ativa, a avaliação dela
e um controle de reversão. O ganho é limitado pelo que os adaptadores entregam. E a política é protegida por
teste, porque vira irreversível no instante em que alguém treina a base.

---

## ADR-0004 Consentimento como pré-condição para coleta, retenção e aprendizado

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** Os motores de memória e de experiência existem para registrar interações, e a interface mostra
métricas de memória e de aprendizado. Se isso virar captura automática de tudo, o produto contradiz a própria
promessa de privacidade. A pesquisa também mostrou que várias bibliotecas prontas de memória para agentes vêm
com provedor remoto por padrão, comportamento inaceitável num produto local-first.

**Decisão.** Cinco regras. Local por padrão: nenhum dado sai do host sem ação explícita, nomeada e auditada, e
dependência que faz egress por padrão não entra sem flag desativada e aviso. Captura seletiva: registrar exige
consentimento por finalidade, ou seja, memória, avaliação ou treinamento, e o consentimento é revogável, com
efeito sobre o uso futuro e revisão do uso passado. Retenção configurável: expiração por tipo de memória,
exportação em formato aberto e exclusão que chega ao armazenamento primário, ao índice de texto completo, ao
índice vetorial, ao KV cache, ao pré-processamento, aos arquivos de write-ahead e de memória compartilhada, às
exportações e aos backups. Rastreabilidade: toda memória e toda entrada de dataset guarda origem, timestamp e
justificativa de seleção, para o sistema conseguir responder por que sabe algo. Auditoria: acesso a dado
pessoal é registrado, e o usuário pode inspecionar, editar e apagar.

**Alternativas consideradas.** Capturar tudo e filtrar depois foi rejeitado: contradiz a promessa, amplia a
superfície de exposição e deixa a exclusão ao acaso. Adotar um framework de memória como dependência central
foi rejeitado pelos padrões remotos, pelo modelo de retenção e pela exclusão que não se consegue garantir; a
taxonomia foi emprestada, a posse dos dados não. Um único prompt de consentimento na instalação não cobre
finalidades distintas nem sustenta revogação de verdade.

**Consequências.** A exclusão vira requisito testável em vários pontos, e o dataset de aprendizado precisa de
versionamento imutável. Dá mais trabalho do que guardar tudo e decidir depois. Apertar é sempre reversível;
afrouxar não é, então todo relaxamento exige novo registro e revisão de risco.

---

## ADR-0005 Pesquisa e arquitetura antes da implementação

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** O plano de execução determina que funcionalidade não deve ser construída antes de a arquitetura
estar de pé. Escrever primeiro o código de runtime, catálogo e memória embutiria decisões de fornecedor no
núcleo, que é exatamente o desfecho que o projeto existe para evitar.

**Decisão.** A primeira fase foi executada como pesquisa verificável: catorze frentes independentes, cada uma
com relatório no repositório privado, fontes abertas primárias em vez de trecho de busca, e um campo
obrigatório de verificação por afirmação, classificado como verificado, parcialmente verificado ou não
verificado. Nenhuma funcionalidade do produto foi implementada antes do encerramento dessa fase. Decisão
técnica que mude um contrato, o stack ou uma promessa de compatibilidade vira registro de decisão com
evidência, e o documento de contexto do projeto é atualizado na mesma entrega.

**Alternativas consideradas.** Prototipar de imediato com um único runtime foi rejeitado porque o protótipo
vira a arquitetura: escolha de fornecedor, modelo de dados e API vazam para o código inteiro. Pesquisa
narrada sem artefato foi rejeitada porque não se refuta nem se reaproveita, e é a evidência versionada que
sustenta tanto as decisões quanto a revisão posterior.

**Consequências.** Várias correções chegaram antes de existir código: um modelo do catálogo inicial não é
executável localmente, a NPU não é rota geral de inferência, Vulkan precede ROCm na plataforma AMD alvo, e o
footprint de KV em contexto longo descarta configurações que o material do produto dava como certas. O custo é
tempo de calendário no começo, compensado pelo retrabalho evitado. Pesquisa não é irreversível: evidência nova
pode substituir um registro, e o registro substituído continua marcado como tal.

---

## ADR-0006 Compatibilidade declarada apenas com evidência de teste

**Status:** aceito. **Data:** 2026-11-21.

**Contexto.** Este mercado mistura afirmação de marketing com afirmação de engenharia. Frases como "roda um
modelo de 120B" ou "usa a NPU" muitas vezes não passam na aritmética de banda de memória e de tamanho de
cache. O produto roda em hardware que o usuário já tem, então uma compatibilidade errada prejudica a
confiança no produto e na máquina.

**Decisão.** Compatibilidade é estado verificado, nunca inferência a partir de nome de fornecedor, contagem de
parâmetros ou número nominal de TOPS. Seis estados são obrigatórios: testado, não validado, compatível com
limitações, incompatível, requer instalação, requer hardware adicional. Todo estado carrega registro de
ambiente: sistema operacional e versão, kernel e driver, runtime e commit, backend, dispositivo, carveout de
memória quando aplicável, hash do artefato, quantização, contexto configurado, concorrência testada, métricas
medidas e data. Sem registro, o estado mais alto que se pode publicar é "não validado". Número mostrado na
interface vem da medição do próprio aplicativo; benchmark de terceiros pode aparecer como referência
identificada, nunca como expectativa do produto.

**Alternativas consideradas.** Matriz estática mantida à mão envelhece na velocidade dos drivers e esconde que
ninguém testou. Rodar um smoke test e marcar a combinação como compatível ignora contexto longo, concorrência
e estabilidade, e justifica no máximo "não validado" ou "com limitações". Faixa genérica como "modelos
grandes" é jeito educado de não dizer nada e empurrar a decisão para o usuário.

**Consequências.** O produto precisa de instrumentação e de um pipeline de qualificação como trabalho
permanente, e haverá modelo que o aplicativo se recusa a oferecer em determinada máquina. Essa recusa é
comportamento correto e precisa aparecer assim na interface. Endurecer a política custa pouco; afrouxá-la
exige tirar informação do usuário.

---

## ADR-0007 Motor independente da interface

**Status:** aceito, com o shell desktop pendente de um protótipo medido. **Data:** 2026-11-21.

**Contexto.** O motor precisa seguir utilizável se a interface for trocada por outro aplicativo ou por um
cliente compatível, e o shell desktop é uma camada multiplataforma ainda a ser escolhida por medição. Motor
nascido dentro do processo da interface transforma essa troca em reescrita.

**Decisão.** Distribuir o motor como biblioteca importável e como serviço local, com a mesma superfície
pública em três caminhos: API interna tipada, ferramenta de linha de comando e gateway compatível com OpenAI.
A interface desktop é cliente, não detém estado canônico e não decide runtime. O shell inicial está proposto
como Tauri 2, com o motor Python em sidecar, e depende de um protótipo que meça memória residente, tamanho do
instalador, comportamento de processo e custo do webview nos três sistemas operacionais. A escolha final vira
registro próprio quando esse protótipo existir. A superfície de rede escuta em loopback por padrão, mantém
acesso cross-origin fechado, autentica mesmo localmente, guarda a chave como verificador e exige ação
explícita do usuário, com aviso, antes de qualquer alcance mais amplo.

**Alternativas consideradas.** Motor embutido no processo da interface viola o requisito de que o núcleo
sobreviva a uma troca de interface e acopla os ciclos de release. Só HTTP, sem biblioteca, abre mão da tipagem
e torna o teste interno lento, porque força serialização dentro de um processo. Escolher Electron sem medição
pode até dar certo, mas seria decisão por hábito, não por dado.

**Consequências.** O contrato público é versionado, duas superfícies precisam de teste, e a linha de comando
tem de continuar funcional como ferramenta de diagnóstico. Trocar o shell afeta apenas o diretório da
aplicação, que é o ponto da decisão.
