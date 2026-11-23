# Segurança e privacidade

Este documento descreve o modelo de segurança estabelecido durante a fase de arquitetura. É um documento de
design. Nenhum controle descrito aqui está implementado, e nada disto deve ser lido como afirmação sobre
software em execução. A seção sobre garantias diz isso de forma direta.

## Ativos a proteger

Conversas, memórias e qualquer dado pessoal que o usuário escolha registrar. Artefatos de modelo e o espaço em
disco que consomem. A chave da API local e qualquer credencial concedida a uma ferramenta ou a um agente. A
trilha de auditoria, que precisa permanecer confiável mesmo quando o usuário é o atacante. A integridade da base
de modelos e dos adaptadores derivados de dados do usuário. A máquina do usuário, ou seja, seus arquivos, sua
posição de rede e seus outros processos.

## Fronteiras de confiança

Quatro fronteiras importam.

A fronteira do host. Tudo dentro da máquina é tratado como dado do usuário, e nada cruza para fora sem uma ação
explícita, nomeada e auditada. Não há telemetria padrão, nem provedor remoto padrão, nem canal de atualização
silencioso.

A fronteira de processo. O motor, os adaptadores de runtime e qualquer execução de ferramenta são preocupações
separadas. A interface é um cliente e não detém estado canônico, então uma interface comprometida ou substituída
não pode se tornar a fonte da verdade.

A fronteira do modelo. Um artefato de modelo é entrada não confiável. Um arquivo baixado é verificado por
checksum contra uma fonte oficial antes de ser usado, e o template, o parser de ferramentas e os metadados de um
modelo são tratados como dados a validar, não como instruções a seguir.

A fronteira da ferramenta. Um servidor MCP, um comando de shell, um caminho de arquivo ou uma chamada de rede
alcançam algo fora do estado do próprio motor. Cada um é uma operação privilegiada, e o motor de políticas fica
entre a requisição e o efeito.

## Ameaças consideradas

Injeção de prompt por conteúdo recuperado, documentos ou saída de ferramenta, levando um agente a agir além do
mandato. Permissões de ferramenta amplas demais concedidas uma vez e herdadas para cima. Um endpoint local exposto
à rede por um binding padrão, e uma chave que protege alguns endpoints mas não todos. Exfiltração de dados por uma
dependência cujo comportamento padrão é um serviço remoto. Captura silenciosa de conversas que o usuário acreditava
serem privadas, e exclusão que deixa cópias em um índice de texto completo, em um índice vetorial, em um cache ou
em um backup. Envenenamento de dados de treinamento por feedback do usuário ou por texto recuperado, e um
adaptador degradado promovido sem aviso. Artefatos de modelo que executam comportamento inesperado pelo template ou
pelo formato. Credenciais aparecendo em logs ou em registros de memória.

Duas ameaças são específicas deste produto. A primeira é uma afirmação de compatibilidade que induz o usuário a
carregar algo que a máquina não sustenta, o que é um problema de confiabilidade com consequência de segurança
quando o modo de falha é esgotamento de memória sob carga. A segunda é uma afirmação de isolamento que o sistema
operacional não consegue honrar, onde a interface diz "em sandbox" enquanto o processo está apenas restrito.

## Controles projetados

**Motor de políticas, negar por padrão.** Toda ação sensível pede permissão e recebe um escopo ou uma recusa. O
privilégio é mínimo, e a herança nunca amplifica: um contexto filho não pode deter uma capacidade que o pai não
tinha. As aprovações vinculam o payload, o recurso, a ferramenta e uma janela de validade, de modo que uma
aprovação não pode ser reaproveitada contra uma requisição diferente. Decisões e aprovações são acrescentadas a uma
trilha de auditoria que suporta revogação e nunca é reescrita no lugar.

**Isolamento de capacidades.** A execução de trabalho não confiável usa o que a plataforma realmente oferece:
seccomp com Landlock no Linux, AppContainer com job objects no Windows, App Sandbox no macOS. Cada backend declara
as capacidades que consegue impor. Quando a plataforma não consegue fornecer a proteção solicitada, a operação
falha fechado com uma mensagem visível. A interface precisa reportar a proteção realmente aplicada, não a
pretendida.

**Consentimento e auditoria.** Captura de memória, uso de dados para avaliação e uso de dados para treinamento são
finalidades separadas com consentimentos separados, e o consentimento é revogável com efeito sobre o uso futuro.
Todo registro de memória e toda entrada de dataset mantém origem, timestamp e justificativa de seleção, de modo que
o sistema consiga responder por que sabe algo e por que determinado exemplo foi usado. O acesso a dados pessoais é
registrado.

**Fronteira de dados local-first.** O armazenamento canônico é um banco de dados local em modo write-ahead, com um
índice de texto completo e um índice vetorial intercambiável. A exclusão é projetada para alcançar o registro
primário, o índice de texto completo, o índice vetorial, os KV caches, artefatos de pré-processamento, arquivos de
write-ahead e de memória compartilhada, exportações e backups. Uma dependência que faz egress de rede por padrão não
entra no produto sem uma flag desativada e um aviso. A API local escuta em loopback, mantém o acesso cross-origin
fechado, autentica mesmo na mesma máquina, armazena a chave como verificador em vez de texto puro e exige uma ação
explícita do usuário antes de qualquer alcance de rede mais amplo. A descoberta de rede anuncia o serviço, nunca um
segredo.

**Gates de artefato e de licença.** Os downloads vêm de fontes oficiais com verificação de checksum antes de o
artefato ser marcado como instalado. Licenças de modelo são um campo do catálogo, e um modelo cuja licença exige
aceitação não é oferecido para download antes de o usuário aceitá-la, com o aceite registrado.

## O que não está garantido

Nada está implementado, então nada está garantido. Não há serviço em execução, binário, chave ou armazenamento de
dados para testar, e este repositório não deve ser lido como evidência de que qualquer item acima funciona.

Mesmo depois de implementado, o design não pode prometer que o isolamento equivale à melhor proteção disponível da
plataforma em toda versão, porque as primitivas variam por kernel e por release de sistema operacional e algumas
configurações vão degradar. Não pode prometer que apagar texto remove tudo o que um adaptador derivado aprendeu,
razão pela qual a exclusão precisa alcançar adaptadores e pela qual o teste de memorização é requisito, não
refinamento. Não pode prometer que um juiz automático detecta toda regressão de qualidade. E não pode prometer que
um runtime, driver ou modelo de terceiros se comporta como documentado.

## Relatar um problema

Não existe produto em execução nem processo de resposta a incidentes de segurança associado a este repositório. Se
você encontrar um erro nestes documentos, uma inconsistência entre uma afirmação e a fonte declarada por ela, ou uma
fraqueza de design no modelo descrito acima, abra uma issue no repositório com a seção e o raciocínio. Não inclua
credenciais, dados pessoais ou detalhes de um sistema de terceiros em uma issue pública.
