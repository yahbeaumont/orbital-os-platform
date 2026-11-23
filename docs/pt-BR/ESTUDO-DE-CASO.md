# Estudo de caso: desenhar uma estratégia de runtime independente de hardware antes de escrever código

## O que o trabalho precisava entregar

ORBITAL OS é uma plataforma de IA desktop feita para rodar na linha de hardware ORBITAL e em máquinas de
outros fabricantes, em três sistemas operacionais. Antes de qualquer parte dela existir, o projeto precisava
de uma estratégia de runtime: qual motor de inferência roda em qual máquina, como se decide que um modelo
cabe na memória e como o produto continua aprendendo sem deixar de ser auditável.

A entrega foi documentação: 57 arquivos, cerca de 4.000 linhas, 14 relatórios de pesquisa com fontes
primárias, 7 registros de decisão, 5 diagramas, 5 commits. Código de produção: nenhum. O valor não está no
volume: várias premissas morreram antes de virarem arquitetura.

## O problema, em termos concretos

Três perguntas precisam de resposta antes de o primeiro token ser gerado. Que hardware está de fato presente?
Qual runtime consegue usá-lo? Este modelo cabe na memória, neste comprimento de contexto, com espaço para o
sistema operacional?

Para cada uma existe uma resposta barata e errada. O hardware sai da folha de especificação, mas a folha
descreve uma família de produtos, não a máquina à frente do usuário. O runtime é escolhido por reputação, e
cada um conta uma história diferente em AMD, NVIDIA, Intel, Apple e CPU pura. O encaixe do modelo é estimado
por contagem de parâmetros e largura de bits nominal, o que ignora o KV cache, o overhead de runtime e o fato
de que o arquivo "4 bits" de um fornecedor não tem quatro bits por peso.

O modo de falha não é uma queda na primeira requisição. É o produto declarar um modelo como suportado, baixar
dezenas de gigabytes, responder duas perguntas e morrer no token 3.000, quando o cache cresce. Isso é problema
de especificação, e sai barato prevenir no papel.

## Restrições que moldaram o design

Depois de instalado, o produto funciona offline, então o núcleo não pode exigir serviço remoto. Precisa
sobreviver à troca da própria interface, então o motor não pode viver dentro do processo da UI. Precisa ser
honesto sobre privacidade, então captura de memória não pode ser padrão. E não pode depender de um fornecedor
só, o que descarta escolher o runtime em tempo de build.

Duas restrições custaram mais. Qualificação exige hardware que o ambiente de desenvolvimento não tem, então
nenhum estado chega a "testado" com honestidade. E os números públicos de desempenho da plataforma se
contradizem, o que transforma uma questão de benchmark em questão de rastreabilidade.

## O primeiro problema difícil: dimensionar o modelo contra um número em que ninguém concorda

O material do produto descrevia duas configurações, uma com 96 GB de memória unificada e outra com 192 GB.
Benchmarks públicos da mesma família de processador saíram em máquinas de 128 GB. A página do próprio
fornecedor, quando consultada, listava um máximo menor que o da configuração à venda, e o mais alto não se
confirmou em fonte pública primária.

A resposta tentadora é escolher um número e gravá-lo no código. A resposta adotada foi tirar o número do
software. O motor de compatibilidade calcula um orçamento a partir da memória que o sistema operacional
reporta em tempo de execução, soma o resultado de um teste funcional curto por API de aceleração e dimensiona
o modelo contra isso. Os pesos residentes vêm do total de parâmetros e dos bits efetivos por peso, não dos
parâmetros ativos, porque ativação esparsa muda o tráfego, não a residência. O KV cache vem da contagem de
camadas, da contagem de cabeças de KV e da dimensão de cabeça do próprio artefato, com o tamanho do elemento
explícito. Espaço de scratch e overhead de runtime entram no orçamento, e 20 a 25 por cento da memória fica
reservado para o sistema e o driver.

Essa decisão tem preço. O software agora pode estar correto numa máquina que ninguém testou, o que significa
responder "compatível, não validado" em hardware que o time comercial considera suportado, e o produto não
consegue dizer se roda no Ultra sem aquela unidade na bancada. A alternativa era pior: uma constante no
código, errada em uma das três configurações.

## O segundo problema difícil: uma abstração escrita antes das implementações

Escrever o contrato de runtime antes de qualquer adaptador é apostar no que os runtimes têm em comum. A
comparação tornou a aposta visível. Um expõe controle fino sobre contexto, quantização e KV cache, com
concorrência moderada. Outro esconde esses controles atrás de padrões que não batem com os do primeiro. Um terceiro
é feito para throughput e não roda nativamente em um dos sistemas operacionais alvo. Um quarto exige código
por arquitetura, e um quinto só faz sentido em hardware Apple.

Duas propriedades saíram dessa comparação. Cada método declara suas capacidades, então o adaptador diz o que
faz em vez de falhar no ponto da chamada. E simulação é defeito: adaptador que não faz streaming avisa, e o
chamador vê uma limitação declarada, não uma resposta de aparência plausível que não corresponde ao que
aconteceu. Escolher runtime é decisão de roteamento, tomada com o veredito de compatibilidade como entrada,
nunca decisão do chamador. Com isso, comportamento específico de fornecedor fica fora da superfície do próprio
produto.

O trade-off é manutenção. Todo adaptador carrega uma matriz de validação por sistema operacional, backend e
dispositivo, e adaptador não testado é pior que nenhum adaptador, porque transforma recusa honesta em
incidente. A lista inicial é curta, e desativar um adaptador é a resposta correta quando falta cobertura.

## O terceiro problema difícil: um gate de aprendizado sem nada para avaliar

"Aprende com você" é o recurso que mais facilmente destrói credibilidade, porque a implementação óbvia,
treinar o modelo base sobre a atividade do usuário, tira de uma vez o rollback, a remoção e a explicação. O
design congela a base e faz o aprendizado produzir artefatos: preferências e instruções de contexto numa
camada reversível, adaptadores versionados numa camada mais lenta.

O candidato é comparado ao adaptador corrente sobre um conjunto de avaliação congelado, com comparação pareada
e estimativa por reamostragem da diferença, mais checagens de regressão nas capacidades que ele não devia
alterar. A promoção é decisão registrada, e a versão anterior continua carregável, então rollback é troca de
ponteiro, não restauração. O design já mostra o custo: o Motor de Avaliação precisa existir antes de o Motor
de Aprendizado servir para algo, o que inverte a ordem de construção intuitiva.

## O que a pesquisa mudou

Cinco conclusões substituíram premissas anteriores. Um modelo listado como pronto para produção não é
executável localmente: o checkpoint oficial tem backbone de 552B, cerca de 315 GiB de pesos residentes na
quantização que o plano assumia. Quatro modelos de fronteira têm pesos abertos e ficam categoricamente fora da
memória de um laptop, então o lugar deles no catálogo é a descoberta, não a execução. A NPU não é rota geral
de inferência para esta classe de modelo, porque não há caminho direto documentado para o formato de artefato
em uso, então ela vira adaptador opcional com allowlist. Na plataforma AMD alvo, Vulkan precede ROCm na
qualificação inicial, porque a documentação do próprio fornecedor limita o stack ROCm em um dos sistemas
operacionais. E a capacidade de memória da configuração alta ainda precisa de confirmação, sem impacto no
software.

Um número atribuído ao hardware, de 104 a 128 tokens por segundo para um modelo com backbone de 552B e 16B de
parâmetros ativos por token, nunca foi reproduzido e consta apenas como afirmação de terceiro. Um cálculo de
banda coloca a taxa ideal de decodificação desse conjunto ativo em cerca de 30 tokens por segundo na banda de
memória declarada, antes de cache, kernels e concorrência. A diferença não prova que a afirmação esteja
errada; prova que a afirmação não tem condições registradas. A resposta do design é estrutural: número na
interface vem da medição do próprio aplicativo, e benchmark de terceiros aparece só como referência
identificada.

## O que eu faria diferente

A disciplina de pesquisa valeu a pena, e durou tempo demais como bloco único. Uma primeira passagem mais
enxuta, seguida do menor recorte que um usuário consegue medir (detectar hardware, escolher um runtime,
carregar um modelo, responder um prompt, expor um endpoint), teria produzido as mesmas correções mais cedo:
metade delas veio de aritmética que um sistema rodando teria forçado de qualquer jeito.

Segundo, a fórmula de compatibilidade deveria ser executável desde o primeiro dia. Virou um script pequeno,
que imprime pesos, cache e orçamento com a aritmética à vista, e no mesmo instante contradisse dois números do
material do produto. Uma planilha teria escondido o mesmo erro.

Terceiro, o acesso a hardware deveria ter sido dependência bloqueante, não item de logística posterior. Tudo
aqui que diz "testado" é inalcançável, e documentação não fecha essa lacuna.
