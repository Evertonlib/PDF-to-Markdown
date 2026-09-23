# Conversor PDF → Markdown

Converte arquivos PDF em arquivos Markdown (`.md`) equivalentes. O objetivo é reduzir o consumo de tokens quando você envia PDFs para o Claude — um teste real mostrou cerca de 55% menos tokens usando o `.md` no lugar do PDF original, pro mesmo resumo.

## Antes de usar

Você precisa ter o Python instalado na máquina. Se `python --version` funcionar no terminal, já está tudo certo.

## Instalação (só precisa fazer uma vez)

1. Abra um terminal na pasta deste projeto.
2. Rode:
   ```
   pip install -r requirements.txt
   ```
3. **Esse passo baixa cerca de 90 MB** (a biblioteca de conversão e suas dependências). Pode levar alguns minutos, dependendo da internet — é normal, não travou.

## Como usar

1. Coloque os PDFs que você quer converter dentro da pasta `a_converter/`.
2. Dê **duplo clique em `converter.py`**. Isso abre um terminal com um menu mostrando os PDFs encontrados.
   - Alternativa, se preferir: abra um terminal nesta pasta e rode `python converter.py`.
3. Escolha no menu: o número de um PDF específico, `0` para converter todos de uma vez, ou `Q` para sair sem converter nada.
4. Pronto. O `.md` aparece do lado do PDF, dentro de `a_converter/`, com o mesmo nome.

## O que esperar

- Rodar de novo sobre o mesmo PDF **sobrescreve o `.md` sem avisar** — é o comportamento esperado.
- Assim que a conversão termina, a janela do terminal **fecha sozinha** — não precisa apertar nada.
- O PDF original nunca é alterado; só o `.md` é criado ao lado dele.

## Limitações desta versão

- **PDFs escaneados** (sem texto selecionável, só imagem) não são suportados — o `.md` gerado fica vazio ou quase vazio, e a ferramenta avisa quando isso acontece.
- **PDFs protegidos por senha** não são suportados — são reportados como erro e pulados.
