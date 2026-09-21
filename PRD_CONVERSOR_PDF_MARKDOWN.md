# PRD — Conversor PDF → Markdown

## 1. Objetivo

Criar uma ferramenta de linha de comando, de uso local, que converte arquivos PDF em arquivos Markdown (.md) equivalentes, com o único propósito de reduzir o consumo de tokens quando o Everton envia PDFs para o Claude (trabalho, faculdade, projeto pessoal AA, condomínio).

Um teste manual já realizado pelo Everton confirmou redução real de aproximadamente 55% no consumo de tokens ao enviar o conteúdo em Markdown em vez do PDF original, para o mesmo prompt de resumo. O valor da feature já está validado empiricamente — este PRD trata apenas de como construir a ferramenta, não de justificar se ela vale a pena.

Este é um projeto novo e isolado, em repositório próprio (`PDF to Markdown`), sem nenhuma integração com outros sistemas ou automações do Everton (não confundir com Checklist-Dinamica, automações da By Arabi ou qualquer outro repositório).

## 2. Estado atual do projeto

A pasta do projeto ainda não tem nenhum código, script ou estrutura de pastas — a implementação será construída do zero. O único arquivo presente na raiz, além deste PRD, é `PES_TEC_SOC_COMP_ACE_2021.pdf`, um trabalho de faculdade real do Everton (~4,2 MB) adicionado como exemplo do tipo de PDF que a ferramenta vai converter. Ele não está dentro da futura pasta `a_converter/` e não representa um requisito novo — é apenas um dado de contexto disponível, que pode servir de caso de teste manual durante a implementação (bastando movê-lo para `a_converter/` quando a ferramenta existir). Não há repositório Git próprio inicializado dentro de `PDF to Markdown` no momento desta pesquisa (a pasta está apenas fisicamente dentro da árvore `AUTOMACOES`, mas o Everton pediu que este projeto seja tratado como isolado, em repositório próprio). Não há, portanto, "scripts existentes" deste projeto para reaproveitar.

Também não foi encontrado, em outros repositórios do Everton (ex.: Checklist-Dinamica), nenhum script Python com menu interativo de terminal que pudesse servir de padrão de referência. Ou seja, não há convenção interna herdada a seguir; as decisões de estilo abaixo são novas e valem apenas para este projeto.

## 3. Decisões já tomadas pelo Everton (restrições não negociáveis)

Estas decisões vêm do pedido original e devem ser tratadas como resolvidas, não como pontos em aberto:

1. **Sem custo financeiro nem dependência de serviço de IA externo.** A restrição do Everton não é "nenhuma rede neural pode participar do pipeline" — é que a ferramenta não pode exigir integração com um módulo de IA externo, não pode exigir credencial ou chave de API, e não pode gerar custo financeiro recorrente (crédito, recarga ou mensalidade de plataforma tipo Anthropic, DeepSeek, Minimax etc.). Um modelo de rede neural que roda **localmente**, embutido na própria dependência instalada via pip, sem nenhuma chamada de rede em tempo de execução e sem custo financeiro, **atende a esse critério** — mesmo que use inferência de modelo internamente. A ferramenta continua sendo um pré-processador de texto, não um resumidor: seu papel é reestruturar o conteúdo já existente no PDF em Markdown, sem gerar, resumir ou interpretar conteúdo novo (ver também seção 9). Espera-se que rodar o mesmo PDF várias vezes na mesma máquina produza sempre o mesmo Markdown — teste recomendado na premissa 9.
2. **Interface mínima obrigatória: terminal interativo com menu navegável e perguntas sim/não.** O Everton nunca deve precisar digitar manualmente um caminho de arquivo.
3. **Fluxo operacional fixo:** existe uma pasta `a_converter` dentro do próprio repositório. O Everton coloca PDFs nela, roda a ferramenta, e ela gera o(s) .md correspondentes. Se já existir um .md com o mesmo nome, a ferramenta sobrescreve sem perguntar (não há necessidade de confirmação de sobrescrita).

### 3.1 Nota técnica: modelo de layout do pymupdf4llm

O `pymupdf4llm` ativa por padrão um modelo de layout (rede neural via `onnxruntime`) para reconstruir a ordem de leitura em páginas complexas (colunas, cabeçalhos, tabelas). Ele roda inteiramente local, sem chamada de rede em tempo de execução e sem custo financeiro — atende ao critério da seção 3.

**Decisão deste PRD:** o script usa esse comportamento padrão (layout ativado). A chamada `pymupdf4llm.use_layout(False)` existe e desativaria o modelo, mas não é usada aqui.

## 4. Pesquisa de bibliotecas de conversão (Etapa 2 — padrões externos)

Foram pesquisadas as bibliotecas Python mais citadas para conversão de PDF em Markdown em 2026. Resumo comparativo:

| Biblioteca | Como funciona | Sem custo/API externa (roda local, sem serviço pago)? | Instalação | Adequação ao caso de uso do Everton |
|---|---|---|---|---|
| **pymupdf4llm** | Lê a estrutura interna do PDF via engine C do MuPDF (mesma base do PyMuPDF) e converte para Markdown. Desde a versão 1.27.2.1, ativa por padrão um modelo de layout (rede neural via `onnxruntime`) para reconstruir a ordem de leitura em páginas complexas — ver detalhamento abaixo | Sim. O modelo de layout roda localmente, sem chamada de rede nem custo financeiro (ver seção 3.1) | `pip install pymupdf4llm`. Instala automaticamente 10 pacotes adicionais como dependência obrigatória (não como extra opcional) — ver detalhamento abaixo. Não exige compilador nem Visual C++ Build Tools (todos os pacotes vêm como wheels pré-compilados). Roda em Python ≥3.10 (a máquina do Everton tem 3.14.3, compatível) | Alta. É a opção mais simples entre as pesquisadas, e é adotada com o comportamento padrão da biblioteca, sem necessidade de nenhuma configuração adicional |
| **markitdown** (Microsoft) | Conversor multi-formato (PDF, Word, Excel, PPT, HTML, imagens etc.) para Markdown, pensado para alimentar LLMs | Sim, no modo padrão para PDF (o suporte a LLM é opcional e só entra se explicitamente configurado, ex. para descrever imagens) | `pip install "markitdown[pdf]"` — mais dependências transitivas por ser multi-formato | Média. Qualidade de extração de PDF é relatada como inferior à do pymupdf4llm; motor principal do PDF depende de bibliotecas de terceiros adicionais |
| **marker** | Pipeline de "document understanding" com modelos de layout/OCR próprios, pensado para PDFs científicos complexos (fórmulas, tabelas complexas) | Sim — os modelos rodam localmente, sem API nem custo recorrente | Instalação pesada (inclui dependências de deep learning, ex. torch); recomendado uso de GPU para desempenho aceitável | Baixa — não pela presença de IA/rede neural, mas por overengineering, instalação pesada e dependência de GPU para desempenho aceitável, desproporcional ao caso de uso (texto corrido de trabalho/faculdade/condomínio) |
| **docling** (IBM) | Pipeline de compreensão de documentos com análise de layout, OCR e reconhecimento de tabelas via modelos | Sim — mesma lógica do marker, roda local sem custo nem API externa | Instalação pesada, várias dependências, mais lento | Baixa — mesmo motivo do marker: peso de instalação e complexidade desnecessária para o caso de uso, não o uso de IA em si |
| **pdfplumber + lógica própria** | Biblioteca de extração de texto/tabela; exigiria escrever manualmente a lógica de conversão para Markdown | Sim | `pip install pdfplumber`, sem dependências pesadas | Baixa nesse contexto específico: exigiria construir e manter uma camada de conversão própria (mais código para manter por uma pessoa não-técnica), quando a conversão pronta do pymupdf4llm, mesmo com o layout no comportamento padrão, já resolve o caso de uso |

### Correção importante em relação a uma versão anterior deste PRD

Uma versão anterior deste documento afirmava que o pymupdf4llm "não usa rede neural nem LLM por padrão" e que tinha "dependência única" (`pymupdf`). Essa afirmação valia para versões antigas da biblioteca (série 0.x), mas **não é mais verdadeira na versão publicada hoje no PyPI**. As evidências abaixo foram checadas diretamente na máquina do Everton e na documentação oficial do projeto:

- **Teste real de instalação, feito na máquina do Everton** (`pip install pymupdf4llm --dry-run --report`, em 18/09/2026): o pip resolveu e instalaria 11 pacotes (a própria `pymupdf4llm` mais 10 dependências): `pymupdf`, `pymupdf-layout`, `tabulate`, `psutil`, `PyYAML`, `onnxruntime`, `networkx`, `flatbuffers`, `packaging`, `protobuf` (o pacote `numpy`, também exigido, já estava presente na máquina por outro motivo). O download total medido desses pacotes foi de **aproximadamente 90 MB**, sendo os maiores: `pymupdf-layout` (41 MB), `pymupdf` (19 MB), `onnxruntime` (14 MB) e `numpy` (13 MB).
- **CHANGES.md oficial do repositório** (`github.com/pymupdf/pymupdf4llm`), versão 1.27.2.1: *"Installing the pymupdf4llm package automatically installs pymupdf_layout"* e *"import pymupdf4llm will automatically initialise layout."* — ou seja, a partir dessa versão, o modelo de layout (rede neural, via `onnxruntime`) é instalado e ativado automaticamente, sem ser um "extra" opcional.
- O mesmo CHANGES.md documenta a forma de desativar isso em tempo de execução (`pymupdf4llm.use_layout(False)`), chamada não usada neste PRD. Mesmo se fosse usada, ela não evitaria a instalação dos ~90 MB de dependências (`pymupdf-layout`, `onnxruntime` e afins), que são baixadas e instaladas com `pip install pymupdf4llm` independentemente de serem usadas.
- **Licença do `pymupdf-layout`:** o CHANGES.md (versão 0.2.0) registra explicitamente que *"The PyMuPDF-Layout package is not open-source and has its own license, which is different from PyMuPDF4LLM."* A página do pacote no PyPI confirma: licença dual **GNU AGPL 3.0 ou Licença Comercial Artifex** — o mesmo modelo de licenciamento que o próprio `pymupdf` (dependência-base, também mantida pela Artifex) já usa. Ou seja, não é uma classe de licença nova introduzida por este projeto, mas é uma característica real da pilha de dependências que vale registrar: para uso local e pessoal (sem distribuir o software nem oferecê-lo como serviço a terceiros), a obrigação de divulgação de código-fonte da AGPL tipicamente não é acionada — mas isto não é uma opinião jurídica definitiva, apenas uma constatação de como a licença costuma ser interpretada nesse tipo de uso. Essa consideração de licença é independente de o layout estar ativado ou desativado, já que o pacote é instalado de qualquer forma.

### Decisão final: **pymupdf4llm com comportamento padrão (layout ativado)**

Justificativa, cruzando com os critérios definidos pelo Everton (seção 3):

- **(a) Sem custo, sem API externa, roda localmente:** o modelo de layout (`onnxruntime`) roda inteiramente local, sem chamada de rede em tempo de execução nem custo de API.
- **(b) Roda localmente, sem serviço externo pago:** mantém-se verdadeiro — os pacotes de IA instalados (`onnxruntime` etc.) rodam localmente, sem chamada de rede em tempo de execução nem custo de API, independentemente da configuração de layout.
- **(c) Simplicidade de instalação/manutenção:** a instalação continua sendo um único comando (`pip install pymupdf4llm`) e não exige nenhuma configuração manual complexa (não precisa de compilador, GPU ou Tesseract) — nesse sentido, ainda é mais simples que Marker ou Docling. O download inicial é de ~90 MB (o mesmo, esteja o layout ativado ou desativado, já que a instalação dos pacotes independe do uso em tempo de execução). Isso é aceitável para uma instalação única, mas deve ser esperado pelo Everton (primeira instalação pode demorar alguns minutos, dependendo da internet).
- **(d) Foco em reduzir tokens de texto corrido:** mantém-se — o objetivo é reduzir tokens ao enviar PDFs para o Claude. O modelo de layout, no comportamento padrão (ativado), ajuda a reconstruir a ordem de leitura em páginas complexas (colunas, cabeçalhos, tabelas), o que tende a gerar um Markdown mais fiel ao que um humano leria, sem comprometer o objetivo de redução de tokens — o conteúdo continua sendo reestruturado em texto simples.

O pymupdf4llm, usado com o comportamento padrão da biblioteca, continua sendo a opção recomendada frente às alternativas pesquisadas: é a única que combina instalação em um único comando (sem dependências de sistema como compilador/GPU/OCR externo), uma API de uma linha (`pymupdf4llm.to_markdown(...)`) e comportamento 100% local e sem custo, mesmo usando um modelo de layout embutido. As alternativas com instalação mais leve (`pdfplumber` puro) exigiriam escrever e manter lógica de conversão própria; as alternativas com modelos de layout/OCR mais sofisticados (Marker, Docling) continuam fora de escopo, não por usarem IA, mas por serem overengineering e exigirem instalação pesada (GPU recomendada) para o caso de uso do Everton.

**Escopo de OCR:** por padrão, mesmo com o layout no comportamento padrão (ativado), o pymupdf4llm não roda OCR (não tenta ler texto de páginas escaneadas/imagens). Existe suporte opcional a OCR (`use_ocr=True`), mas ele depende de dependências adicionais e de um mecanismo de reconhecimento de texto em imagem — isso aumentaria ainda mais o tamanho da instalação para pouco ganho, já que os PDFs do Everton (trabalho, faculdade, condomínio) são majoritariamente texto pesquisável, não digitalizações. **Decisão deste PRD: OCR fica fora do escopo da v1.** PDFs compostos só por imagens escaneadas gerarão um Markdown vazio ou quase vazio — ver seção de riscos e critérios de aceitação.

## 5. Relação com scripts existentes

Não há scripts existentes neste projeto (pasta praticamente vazia, à exceção do PDF de exemplo citado na seção 2) nem convenções de outros repositórios do Everton a seguir, conforme constatado na Etapa 1. Esta ferramenta não reaproveita e não se integra com nenhum outro repositório do Everton (Checklist-Dinamica, automações By Arabi, Assistente de E-mail etc.). Essa separação deve ser mantida durante toda a implementação.

## 6. Arquivos afetados

Como o projeto está praticamente vazio, "afetados" aqui significa **criados**:

- Um script principal em Python, na raiz do repositório, responsável por exibir o menu interativo e orquestrar a conversão (nome exato a definir na Spec, ex. `converter.py` ou `main.py`). Este script usa `pymupdf4llm.to_markdown(...)` com o comportamento padrão da biblioteca (ver seção 3.1).
- Um arquivo de dependências (`requirements.txt`) listando `pymupdf4llm` com versão fixada (ex. `pymupdf4llm==1.28.2`) como dependência direta de terceiros — o pip resolve e instala automaticamente as ~10 dependências transitivas listadas na seção 4.
- A pasta `a_converter/` na raiz do repositório, onde o Everton deposita os PDFs a converter. Como pastas vazias não são versionadas pelo Git, será incluído um arquivo marcador (ex. `.gitkeep`) para que a pasta exista logo após clonar o repositório.
- Um `README.md` simples explicando como instalar (passo a passo) e como rodar a ferramenta, escrito em linguagem não-técnica, já que o Everton não é técnico — incluindo um aviso de que a primeira instalação baixa cerca de 90 MB e pode levar alguns minutos.
- Um `.gitignore` básico (para não versionar os próprios PDFs/Markdown que o Everton for colocando em `a_converter/`, nem a pasta de ambiente virtual do Python, se houver).

Nada além disso deve ser criado nesta primeira versão — em particular, nenhum arquivo de configuração de nuvem, nenhuma pasta de "saída" separada (ver premissa 1 na seção 10) e nenhuma automação de agendamento.

## 7. O que será adicionado

- Menu de terminal, com opções numeradas (sem necessidade de digitar caminho de arquivo), que:
  - Lista automaticamente os arquivos PDF encontrados dentro de `a_converter/`.
  - Permite escolher converter um PDF específico da lista, ou todos de uma vez.
  - Faz perguntas de confirmação no formato sim/não quando aplicável (ex.: "Converter todos os 3 PDFs encontrados? (s/n)").
- Lógica de conversão usando `pymupdf4llm`, **com o comportamento padrão da biblioteca (modelo de layout ativado, ver seção 3.1)**, gerando um arquivo `.md` para cada PDF processado, salvo dentro da própria pasta `a_converter/`, com o mesmo nome base do PDF (ex.: `contrato.pdf` → `contrato.md`).
- Sobrescrita silenciosa: se já existir um `.md` com o mesmo nome, ele é substituído sem pedir confirmação (conforme decisão já tomada pelo Everton).
- Mensagens de status no terminal durante a conversão (ex.: "Convertendo contrato.pdf...", "Concluído: contrato.md gerado com sucesso").
- Tratamento de erro por arquivo: se um PDF individual falhar (corrompido, protegido por senha, etc.), a ferramenta registra o erro daquele arquivo no terminal e segue para o próximo, em vez de interromper o processo inteiro.
- Um resumo final ao término da execução (quantos arquivos foram convertidos com sucesso, quantos falharam e por quê).

## 8. O que será removido

Não se aplica — não há nada pré-existente neste projeto para remover.

## 9. O que não será tocado

- Nenhum outro repositório do Everton (Checklist-Dinamica, automações By Arabi, Assistente de E-mail, ou qualquer workspace/skill da pasta `AUTOMACOES`) deve ser lido, editado ou referenciado pela implementação desta ferramenta.
- Nenhuma integração com Claude/Anthropic API, Trello, Google API ou qualquer serviço externo — a ferramenta roda 100% offline após a instalação inicial das dependências. O que é aceitável é o uso de modelo de IA **local**, embutido na dependência instalada via pip (seção 3); integração com serviço de IA externo, credencial de API ou custo recorrente continuam fora de cogitação.
- Nenhuma lógica de resumo, reescrita ou interpretação do conteúdo do PDF — a ferramenta apenas transcreve/reestrutura o texto existente em formato Markdown, sem alterar o conteúdo semântico.
- O conteúdo dos PDFs do Everton em si não é modificado — a ferramenta lê o PDF original e apenas cria um novo arquivo `.md` ao lado dele; o PDF original permanece intacto em `a_converter/`.

## 10. Premissas assumidas

Como parte do pedido deixou pontos operacionais implícitos, este PRD assume o seguinte até que o Everton corrija:

1. **Local de saída do Markdown:** o `.md` gerado fica na mesma pasta `a_converter/`, ao lado do PDF de origem (não foi pedida uma pasta de saída separada). Se o Everton preferir uma pasta `convertidos/` separada, isso deve ser dito antes da Spec.
2. **PDFs protegidos por senha:** serão tratados como erro esperado (a ferramenta não tentará quebrar senha nem pedirá a senha ao usuário) — o arquivo é pulado e reportado no resumo final.
3. **PDFs escaneados (só imagem, sem texto pesquisável):** ficam fora do escopo de extração de texto nesta v1 (sem OCR, ver seção 4). O resultado será um `.md` vazio ou quase vazio; a ferramenta deve pelo menos avisar quando isso acontecer, em vez de silenciosamente gerar um arquivo vazio sem explicação.
4. **Ambiente de execução:** o Everton já tem Python instalado na máquina (confirmado: Python 3.14.3 disponível) e sabe (ou vai aprender, com ajuda do README) a rodar `pip install -r requirements.txt` uma única vez e depois `python nome_do_script.py` sempre que quiser converter algo. Não está no escopo desta v1 criar um instalador `.exe` nem um atalho de duplo clique — se o Everton quiser isso, é um pedido adicional a ser avaliado à parte.
5. **Menu de terminal simples:** será implementado como menu numerado por texto (o Everton digita o número da opção e aperta Enter), usando apenas recursos nativos do Python (sem biblioteca extra de interface, tipo `questionary` ou `simple-term-menu`). Isso já atende ao requisito de "nunca precisar digitar caminho de arquivo" com o menor número de dependências extras possível, evitando problemas de compatibilidade dessas bibliotecas com o terminal do Windows.
6. **Nomes de arquivo duplicados/conflitantes:** se dois PDFs na pasta tiverem nomes que geram o mesmo `.md` (ex. por diferença só de maiúscula/minúscula em sistemas sensíveis a caixa), o comportamento seguirá a mesma regra de sobrescrita silenciosa, na ordem em que forem processados.
7. **Instalação inicial com internet:** a primeira instalação (`pip install -r requirements.txt`) exige conexão com a internet para baixar os ~90 MB de pacotes descritos na seção 4. Uso posterior da ferramenta (conversões do dia a dia) não exige internet.
8. **Arquivo de exemplo real disponível para teste manual:** o Everton adicionou `PES_TEC_SOC_COMP_ACE_2021.pdf` (um trabalho de faculdade dele) na raiz do repositório. Ele não é tratado como requisito novo nem foi analisado a fundo neste PRD — é apenas um exemplo real do tipo de PDF que a ferramenta vai converter, disponível como caso de teste manual durante a implementação (inclusive para o teste de reprodutibilidade citado na premissa seguinte).
9. **Reprodutibilidade execução-a-execução com o layout ativado é esperada, mas não foi testada empiricamente ainda.** Sob o comportamento padrão do pymupdf4llm, não há elementos documentados de aleatoriedade nem chamada de rede no processo de inferência do modelo de layout, então é razoável esperar que converter o mesmo PDF várias vezes, na mesma máquina e mesma versão da biblioteca, produza sempre o mesmo Markdown. Essa expectativa ainda não foi verificada na prática (diferente da redução de 55% de tokens, que já foi testada pelo Everton). Recomenda-se, durante a implementação, um teste manual simples: converter o mesmo PDF (por exemplo, `PES_TEC_SOC_COMP_ACE_2021.pdf`) duas vezes seguidas e comparar os `.md` gerados. Se alguma variação for observada, isso deve ser tratado como desvio a esclarecer antes de prosseguir, não como algo a ignorar.

## 11. Riscos identificados

- **Comportamento padrão (layout ativado) prioriza fidelidade de leitura em vez de estrutura puramente sequencial.** O modelo de layout tenta reconstruir a ordem de leitura em páginas complexas (colunas, cabeçalhos, tabelas), o que pode introduzir pequenas variações de formatação em PDFs com layout irregular — trade-off aceito nesta versão do PRD (fidelidade em vez de rigidez estrutural). Reprodutibilidade execução-a-execução ainda não foi testada na prática (ver premissa 9).
- **Instalação inicial mais pesada do que o esperado.** A instalação de `pymupdf4llm` baixa cerca de 90 MB em 10 pacotes adicionais (incluindo `onnxruntime`, usado pelo modelo de layout, mantido ativado). Isso é maior do que uma "dependência única leve", mas ainda é um único comando de instalação, sem necessidade de compilador ou configuração manual. Mitigado por avisar isso com clareza no README.
- **Dependência transitiva (`pymupdf-layout`) com licença dual AGPL/comercial**, diferente da licença do próprio `pymupdf4llm`. Para uso pessoal e local, sem distribuição do software nem oferta como serviço, isso tende a não ser um problema prático — mas fica registrado como característica da pilha de dependências, não como uma avaliação jurídica definitiva.
- **Qualidade de extração variável conforme o PDF de origem.** PDFs com layout muito complexo (múltiplas colunas, tabelas elaboradas, PDFs gerados a partir de imagens/scans) ainda podem gerar Markdown com formatação imperfeita ou incompleta, mesmo com o modelo de layout ativado — ele ajuda a reconstruir a ordem de leitura, mas não garante reconstrução perfeita em todos os casos.
- **PDFs escaneados sem OCR resultam em pouco ou nenhum conteúdo extraído**, o que pode confundir o Everton se ele não perceber o motivo. Mitigação: a ferramenta deve avisar explicitamente quando um `.md` gerado ficar vazio ou muito pequeno em relação ao PDF original.
- **Dependência de uma biblioteca de terceiros mantida por outra organização** (`pymupdf4llm`, mantida pelo próprio time do PyMuPDF). Risco de mudanças de comportamento em versões futuras — por exemplo, a própria introdução do modelo de layout por padrão, descoberta nesta pesquisa, é um exemplo de mudança de comportamento entre versões. Mitigado por fixar a versão exata no `requirements.txt`.
- **Sobrescrita silenciosa de `.md`** é uma decisão intencional do Everton, mas carrega risco de perda de uma versão editada manualmente de um `.md` anterior (ex. se ele tiver ajustado o Markdown manualmente e depois rodar a conversão de novo por engano). Como o Everton pediu explicitamente esse comportamento, ele é aceito, mas fica registrado aqui como risco assumido, não ignorado.
- **Redução de 55% é uma estimativa de um teste, não uma garantia por PDF.** A economia real de tokens varia conforme o tipo de documento (PDFs com muitas tabelas/imagens tendem a converter pior do que texto corrido).

## 12. Critérios de aceitação

Cada cenário abaixo descreve entrada, ação e resultado esperado.

1. **Conversão de um único PDF de texto corrido.** Entrada: pasta `a_converter/` contém um único arquivo `relatorio.pdf`, com texto pesquisável (não escaneado). Ação: o Everton roda a ferramenta e escolhe converter esse arquivo. Resultado esperado: é criado `a_converter/relatorio.md` com o conteúdo textual do PDF em Markdown, e o terminal mostra mensagem de sucesso.

2. **Conversão de múltiplos PDFs de uma vez.** Entrada: pasta `a_converter/` contém 3 PDFs válidos. Ação: o Everton escolhe a opção "converter todos" e confirma com "s" na pergunta de confirmação. Resultado esperado: são gerados 3 arquivos `.md` correspondentes, e o resumo final informa "3 de 3 convertidos com sucesso".

3. **Pasta `a_converter` vazia.** Entrada: nenhum arquivo PDF dentro de `a_converter/`. Ação: o Everton roda a ferramenta. Resultado esperado: a ferramenta informa claramente que não há PDFs para converter e orienta a colocar arquivos na pasta antes de tentar de novo, sem travar ou gerar erro técnico ilegível.

4. **Sobrescrita de `.md` existente.** Entrada: pasta contém `contrato.pdf` e já existe `contrato.md` de uma conversão anterior. Ação: o Everton converte `contrato.pdf` novamente. Resultado esperado: `contrato.md` é sobrescrito com o novo conteúdo, sem nenhuma pergunta de confirmação de sobrescrita.

5. **PDF protegido por senha.** Entrada: pasta contém um PDF criptografado/protegido por senha, junto de outros PDFs normais. Ação: o Everton escolhe converter todos. Resultado esperado: o PDF protegido é reportado como falha (com mensagem entendível, ex. "não foi possível abrir: protegido por senha"), os demais PDFs são convertidos normalmente, e o resumo final lista esse arquivo como erro.

6. **PDF corrompido ou inválido.** Entrada: um arquivo com extensão `.pdf` mas que não é um PDF válido (ex. corrompido). Ação: o Everton tenta converter. Resultado esperado: a ferramenta não trava nem encerra abruptamente; reporta esse arquivo como erro no resumo final e continua processando os demais.

7. **PDF escaneado (sem texto pesquisável).** Entrada: um PDF composto só por imagens de páginas escaneadas, sem camada de texto. Ação: o Everton converte esse arquivo. Resultado esperado: um `.md` é gerado, mas a ferramenta avisa no terminal que o resultado ficou vazio (ou quase vazio) e que esse tipo de PDF (escaneado) não é suportado nesta versão.

8. **Nenhum caminho de arquivo digitado manualmente em nenhum momento.** Entrada: qualquer uso normal da ferramenta, do início ao fim. Ação: o Everton interage apenas escolhendo números de menu e respondendo sim/não. Resultado esperado: em nenhum momento a ferramenta pede para digitar um nome de arquivo ou caminho — toda a seleção de arquivos vem de uma lista mostrada na tela, montada automaticamente a partir do conteúdo de `a_converter/`.

9. **Execução repetida não deixa lixo, e o resultado é reprodutível.** Entrada: o Everton roda a ferramenta várias vezes seguidas sobre os mesmos PDFs (por exemplo, `PES_TEC_SOC_COMP_ACE_2021.pdf`, citado na seção 2), sem alterá-los. Ação: repetir a conversão dos mesmos arquivos. Resultado esperado: o conteúdo dos `.md` gerados é idêntico entre as execuções (expectativa e teste recomendado na premissa 9). Se alguma variação for observada, é um desvio a esclarecer antes de prosseguir.

10. **Isolamento do restante do ambiente do Everton.** Entrada: qualquer execução da ferramenta. Ação: rodar a ferramenta normalmente. Resultado esperado: nenhum arquivo fora da pasta do próprio projeto `PDF to Markdown` é lido, criado ou modificado (em particular, nenhum outro repositório do Everton é tocado).

11. **Primeira instalação informa o tamanho do download.** Entrada: o Everton segue o passo a passo do README pela primeira vez em uma máquina nova. Ação: ele roda `pip install -r requirements.txt`. Resultado esperado: o README já avisou previamente que esse passo baixa cerca de 90 MB e pode levar alguns minutos, então o Everton não estranha a demora nem acha que algo travou.

---

**Próximo passo:** este PRD aguarda aprovação do Everton antes de seguir para a Spec. Nenhuma implementação deve começar antes dessa aprovação explícita.
