# Segurança e privacidade

Este documento descreve o modelo de segurança estabelecido na fase de arquitetura. É um documento de design.
Nenhum controle descrito aqui está implementado, e nada disto deve ser lido como afirmação sobre software em
execução. A seção sobre garantias diz isso com clareza.

## Ativos a proteger

Conversas, memórias e qualquer dado pessoal que o usuário decida registrar. Artefatos de modelo e o espaço em
disco que ocupam. A chave da API local e toda credencial concedida a uma ferramenta ou a um agente. A trilha
de auditoria, que precisa continuar confiável mesmo quando o atacante é o próprio usuário. A integridade da
base de modelos e dos adaptadores derivados de dados do usuário. A máquina do usuário: seus arquivos, sua
posição na rede e seus outros processos.

## Fronteiras de confiança

Quatro fronteiras importam.

A do host. Tudo dentro da máquina é dado do usuário, e nada sai sem ação explícita, nomeada e auditada. Não
existe telemetria padrão, provedor remoto padrão nem canal de atualização silencioso.

A de processo. Motor, adaptadores de runtime e execução de ferramenta são coisas separadas. A interface é
cliente e não detém estado canônico, então interface comprometida ou substituída não vira fonte da verdade.

A do modelo. Artefato de modelo é entrada não confiável. Arquivo baixado passa por verificação de checksum
contra fonte oficial antes de ser usado, e template, parser de ferramentas e metadados de um modelo são dados
a validar, não instruções a seguir.

A da ferramenta. Servidor MCP, comando de shell, caminho de arquivo ou chamada de rede alcançam algo fora do
estado do motor. Cada um é operação privilegiada, e o motor de políticas fica entre o pedido e o efeito.

## Ameaças consideradas

Injeção de prompt por conteúdo recuperado, documento ou saída de ferramenta, levando o agente a agir além do
mandato. Permissão de ferramenta ampla demais, concedida uma vez e herdada para cima. Endpoint local exposto à
rede por binding padrão, e chave que protege alguns endpoints mas não todos. Exfiltração de dados por
dependência cujo comportamento padrão é um serviço remoto. Captura silenciosa de conversas que o usuário
acreditava privadas, e exclusão que deixa cópia no índice de texto completo, no índice vetorial, num cache ou
num backup. Envenenamento de dados de treinamento por feedback do usuário ou por texto recuperado, e adaptador
degradado promovido sem aviso. Artefato de modelo que executa comportamento inesperado pelo template ou pelo
formato. Credencial que aparece em log ou em registro de memória.

Duas ameaças são específicas deste produto. A primeira é a afirmação de compatibilidade que leva o usuário a
carregar algo que a máquina não sustenta, problema de confiabilidade com consequência de segurança quando o
modo de falha é esgotamento de memória sob carga. A segunda é a afirmação de isolamento que o sistema
operacional não consegue honrar: a interface diz "em sandbox" enquanto o processo está apenas restrito.

## Controles projetados

**Motor de políticas, negar por padrão.** Toda ação sensível pede permissão e recebe um escopo ou uma recusa. O
privilégio é mínimo, e a herança nunca amplifica: contexto filho não detém capacidade que o pai não tinha.
Cada aprovação vincula payload, recurso, ferramenta e janela de validade, e assim não se reaproveita contra
outra requisição. Decisões e aprovações entram numa trilha de auditoria que admite revogação e nunca é
reescrita no lugar.

**Isolamento de capacidades.** Trabalho não confiável roda com o que a plataforma de fato oferece: seccomp com
Landlock no Linux, AppContainer com job objects no Windows, App Sandbox no macOS. Cada backend declara as
capacidades que consegue impor. Quando a plataforma não fornece a proteção pedida, a operação falha em modo fail
closed, com mensagem visível. A interface precisa reportar a proteção aplicada, não a pretendida.

**Consentimento e auditoria.** Captura de memória, uso de dados para avaliação e uso de dados para treinamento
são finalidades distintas, com consentimentos distintos, e o consentimento é revogável com efeito sobre o uso
futuro. Todo registro de memória e toda entrada de dataset guarda origem, timestamp e justificativa de
seleção, então o sistema responde por que sabe algo e por que usou determinado exemplo. Acesso a dado pessoal
fica registrado.

**Fronteira de dados local-first.** O armazenamento canônico é um banco local em modo write-ahead, com índice
de texto completo e índice vetorial intercambiável. A exclusão foi desenhada para chegar ao registro primário,
ao índice de texto completo, ao índice vetorial, aos KV caches, aos artefatos de pré-processamento, aos
arquivos de write-ahead e de memória compartilhada, às exportações e aos backups. Dependência que faz egress
de rede por padrão não entra no produto sem flag desativada e aviso. A API local escuta em loopback, mantém
acesso cross-origin fechado, autentica mesmo na mesma máquina, guarda a chave como verificador em vez de texto
puro e exige ação explícita do usuário antes de qualquer alcance de rede mais amplo. A descoberta de rede
anuncia o serviço, nunca um segredo.

**Gates de artefato e de licença.** Download vem de fonte oficial com verificação de checksum antes de o
artefato ser marcado como instalado. Licença de modelo é campo do catálogo, e modelo cuja licença exige aceite
não é oferecido para download antes do aceite do usuário, que fica registrado.

## O que não está garantido

Nada está implementado, então nada está garantido. Não há serviço rodando, binário, chave ou armazenamento de
dados para testar, e este repositório não deve ser lido como evidência de que algo acima funciona.

Mesmo depois de implementado, o design não pode prometer que o isolamento equivale à melhor proteção que a
plataforma oferece em toda versão, porque as primitivas mudam conforme o kernel e a release do sistema
operacional e algumas configurações vão degradar. Não pode prometer que apagar o texto remove tudo o que um
adaptador derivado aprendeu, e é por isso que a exclusão precisa chegar aos adaptadores e que o teste de
memorização é requisito, não refinamento. Não pode prometer que um juiz automático detecta toda regressão de
qualidade. Nem que runtime, driver ou modelo de terceiros se comporta como a documentação diz.

## Relatar um problema

Não existe produto em execução nem processo de resposta a incidentes de segurança ligado a este repositório. Se
você encontrar erro nestes documentos, inconsistência entre uma afirmação e a fonte que ela declara, ou
fraqueza de design no modelo descrito acima, abra uma issue no repositório com a seção e o raciocínio. Não
inclua credenciais, dados pessoais ou detalhes de sistema de terceiros em issue pública.
