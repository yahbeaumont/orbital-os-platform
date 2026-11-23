# Estudo de caso: projetando uma estratégia de runtime agnóstica de hardware antes de escrever código

## O que o trabalho precisava produzir

ORBITAL OS é uma plataforma de IA desktop destinada a rodar na linha de hardware ORBITAL e nas máquinas de
outros fabricantes, em três sistemas operacionais. Antes de qualquer parte dela existir, o projeto precisava de
uma estratégia de runtime: qual motor de inferência roda em qual máquina, como se decide que um modelo cabe na
memória e como o produto continua aprendendo sem se tornar não auditável.

A saída foi documentação: 57 arquivos, cerca de 4.000 linhas, 14 relatórios de pesquisa com fontes primárias,
7 registros de decisão, 5 diagramas, 5 commits. Não há código de produção. O valor não está no volume: várias
premissas morreram antes de poderem se tornar arquitetura.

## O problema, enunciado de forma concreta

Três perguntas precisam ser respondidas antes de um único token ser gerado. Qual hardware está realmente
presente? Qual runtime consegue usá-lo? Este modelo cabe na memória, neste comprimento de contexto, com espaço
para o sistema operacional?

Cada pergunta tem uma resposta barata e errada. O hardware é tomado de uma folha de especificações, mas a folha
descreve uma família de produtos, não a máquina à frente do usuário. Os runtimes são escolhidos por reputação, e
cada um tem uma história diferente em AMD, NVIDIA, Intel, Apple e CPU pura. O ajuste do modelo é estimado a
partir da contagem de parâmetros e de uma largura de bits nominal, o que ignora o KV cache, o overhead de
runtime e o fato de que um arquivo "4 bits" de um fornecedor não tem quatro bits por peso.

O modo de falha não é uma queda na primeira requisição. É um produto que declara um modelo como suportado,
baixa dezenas de gigabytes, responde duas perguntas e morre no token 3.000, quando o cache cresce. Isso é um
problema de especificação, e barato de prevenir no papel.

## Restrições que moldaram o design

O produto funciona offline após a instalação, então o núcleo não pode exigir um serviço remoto. Precisa
sobreviver à substituição da própria interface, então o motor não pode viver dentro do processo da UI. Precisa
ser honesto sobre privacidade, então a captura de memória não pode ser padrão. E não pode depender de um único
fornecedor, o que descarta uma escolha de runtime fixada em tempo de build.

Duas restrições custaram mais caro. A qualificação exige hardware que o ambiente de desenvolvimento não tem,
então nenhum estado pode alcançar "testado" com honestidade. E os números públicos de desempenho da plataforma
se contradizem, transformando uma questão de benchmark em uma questão de rastreabilidade.

## O primeiro problema difícil: dimensionar um modelo contra um número com o qual ninguém concorda

O material do produto descrevia duas configurações, uma com 96 GB de memória unificada e outra com 192 GB.
Benchmarks públicos para a mesma família de processador foram produzidos em máquinas com 128 GB. A própria
página do fornecedor, quando consultada, listava um máximo menor do que a configuração sendo vendida, e o mais alto
não pôde ser confirmado em fonte pública primária.

A resposta tentadora é escolher um número e codificá-lo. A resposta adotada foi remover o número do software
por completo. O motor de compatibilidade calcula um orçamento a partir da memória que o sistema operacional
reporta em tempo de execução, soma o resultado de um teste funcional curto por API de aceleração e dimensiona o
modelo contra isso. Os pesos residentes vêm do total de parâmetros e dos bits efetivos por peso, não dos
parâmetros ativos, porque ativação esparsa muda o tráfego e não a residência. O KV cache vem da contagem de
camadas, da contagem de cabeças de KV e da dimensão de cabeça do próprio artefato, com o tamanho do elemento
explícito. Espaço de rascunho e overhead de runtime entram no orçamento, e 20 a 25 por cento da memória é
reservado para o sistema e o driver.

Essa decisão tem um custo. O software agora pode estar correto em uma máquina que ninguém testou, o que
significa que às vezes responderá "compatível, não validado" em hardware que a equipe comercial considera
suportado, e o produto não consegue responder "isso roda no Ultra?" sem aquela unidade na bancada. A alternativa
era pior: uma constante no código que está errada em uma das três configurações.

## O segundo problema difícil: uma abstração escrita antes das implementações

Escrever um contrato de runtime antes de escrever qualquer adaptador é uma aposta sobre o que os runtimes têm em
comum. As comparações tornaram essa aposta visível. Um deles expõe controle fino sobre contexto, quantização e KV
cache, com concorrência moderada. Outro esconde esses controles atrás de padrões que diferem do primeiro. Um
terceiro é construído para throughput e não roda nativamente em um dos sistemas operacionais alvo. Um quarto
exige código por arquitetura, e um quinto só faz sentido em hardware Apple.

Duas propriedades saíram dessa comparação. As capacidades são declaradas por método, de modo que um adaptador
afirma o que consegue fazer em vez de falhar no ponto da chamada. E simulação é defeito: um adaptador que não
consegue fazer streaming diz isso, e o chamador vê uma limitação declarada em vez de uma resposta de aparência
plausível que não é real. A seleção de runtime é uma decisão de roteamento tomada com o veredito de
compatibilidade como entrada, nunca uma decisão do chamador, o que mantém comportamento específico de fornecedor
fora da superfície do próprio produto.

O trade-off é manutenção. Todo adaptador carrega uma matriz de validação por sistema operacional, backend e
dispositivo, e um adaptador não testado é pior do que nenhum adaptador, porque converte uma recusa honesta em
incidente. A lista inicial é curta, e desativar um adaptador é a resposta correta para cobertura ausente.

## O terceiro problema difícil: um gate de aprendizado sem nada para avaliar ainda

"Aprende com você" é o recurso que mais facilmente destrói credibilidade, porque a implementação óbvia, treinar o
modelo base sobre a atividade do usuário, remove de uma vez rollback, remoção e explicação. O design congela a
base e faz o aprendizado produzir artefatos: preferências e instruções de contexto em uma camada reversível,
adaptadores versionados em uma camada mais lenta.

Um candidato é comparado ao adaptador corrente sobre um conjunto de avaliação congelado, com comparação pareada
e uma estimativa por reamostragem da diferença, além de checagens de regressão nas capacidades que ele não devia
alterar. A promoção é uma decisão registrada, e a versão anterior permanece carregável, de modo que rollback é
mudança de ponteiro em vez de restauração. O design já mostra o custo: o Motor de Avaliação precisa existir antes
de o Motor de Aprendizado ser útil, o que inverte a ordem de construção intuitiva.

## O que a pesquisa mudou

Cinco conclusões substituíram premissas anteriores. Um modelo listado como pronto para produção não é executável
localmente: o checkpoint oficial tem um backbone de 552B, cerca de 315 GiB de pesos residentes na quantização que
o plano assumia. Quatro modelos de fronteira têm pesos abertos e ficam categoricamente fora da memória de um
laptop, então o lugar deles no catálogo é descoberta, não execução. A NPU não é uma rota geral de inferência para
esta classe de modelo, porque não há caminho direto documentado para o formato de artefato em uso, então ela se
torna um adaptador opcional com uma allowlist. Na plataforma AMD alvo, Vulkan precede ROCm na qualificação
inicial, porque a documentação do próprio fornecedor limita o stack ROCm em um dos sistemas operacionais. E a
capacidade de memória da configuração alta precisa de confirmação, sem impacto em software.

Um número atribuído ao hardware, 104 a 128 tokens por segundo para um modelo com backbone de 552B e 16B de
parâmetros ativos por token, nunca foi reproduzido e está registrado apenas como afirmação de terceiro. Um
cálculo de banda coloca a taxa de decodificação ideal para esse conjunto ativo em cerca de 30 tokens por segundo
na banda de memória declarada, antes de cache, kernels e concorrência. A diferença não prova que a afirmação está
errada; prova que a afirmação não tem condições registradas. A resposta do design é estrutural: números na
interface vêm da medição do próprio aplicativo, e um benchmark de terceiros aparece apenas como referência
identificada.

## O que eu faria diferente

A disciplina de pesquisa valeu a pena, e durou tempo demais como bloco único. Uma primeira passagem mais enxuta,
seguida do menor recorte que um usuário consegue medir (detectar hardware, escolher um runtime, carregar um
modelo, responder um prompt, expor um endpoint), teria produzido as mesmas correções mais cedo: metade delas veio
de aritmética que um sistema em execução teria forçado de qualquer forma.

Segundo, a fórmula de compatibilidade deveria ter sido executável desde o primeiro dia. Ela se tornou um script
pequeno que imprime pesos, cache e orçamento com a aritmética visível, e imediatamente contradisse dois números do
material do produto. Uma planilha teria escondido o mesmo erro.

Terceiro, o acesso a hardware deveria ter sido uma dependência bloqueante em vez de um item de logística
posterior. Tudo aqui que diz "testado" é inalcançável, e documentação não fecha essa lacuna.
