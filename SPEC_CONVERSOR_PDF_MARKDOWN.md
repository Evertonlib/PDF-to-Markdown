# Spec — Conversor PDF → Markdown

Baseado em `PRD_CONVERSOR_PDF_MARKDOWN.md` (aprovado). Este documento detalha as decisões técnicas de implementação que o PRD deixou em aberto (nomes de arquivo, estrutura de funções, tratamento de exceções, textos exatos de terminal). Nenhuma decisão de negócio do PRD é alterada aqui.

## 0. Observação sobre o estado real do repositório

O PRD (seção 2) descreve o projeto como "sem repositório Git próprio inicializado". A verificação feita nesta etapa mostra que isso não é mais verdade no momento da Spec: o repositório já tem um `.git` inicializado, branch `main`, e 3 commits (`fb80bef`, `62f4903`, `e22167f`), todos relacionados à criação e revisão do PRD. Isso não muda nenhuma decisão técnica — só registra que o Git já está pronto para receber os commits desta implementação, sem necessidade de `git init`.

Confirmado também: além do `.git` e do `PRD_CONVERSOR_PDF_MARKDOWN.md`, a raiz contém apenas `PES_TEC_SOC_COMP_ACE_2021.pdf`, exatamente como o PRD descreve. Não há `a_converter/`, script, `requirements.txt`, `README.md` nem `.gitignore` ainda — tudo será criado do zero, conforme seção 6 do PRD.

## 1. Arquivos a criar

| Arquivo | Papel |
|---|---|
| `converter.py` | Script principal (menu + orquestração + conversão) |
| `requirements.txt` | Dependência direta `pymupdf4llm` com versão fixada |
| `a_converter/.gitkeep` | Marcador para a pasta existir após clonar |
| `README.md` | Instruções de instalação e uso, em linguagem não-técnica |
| `.gitignore` | Ignora PDFs/Markdown do usuário em `a_converter/` e ambiente virtual |

Nome do script: **`converter.py`**, na raiz do repositório (decisão desta Spec — o PRD deixou o nome em aberto, seção 6).

## 2. `requirements.txt`

Uma única linha, com `pymupdf4llm` pinado em uma versão exata (`==`), a ser confirmada no momento da implementação via `pip index versions pymupdf4llm` ou consulta ao PyPI — o PRD cita `1.28.2` apenas como exemplo (seção 6), não como número confirmado. A versão escolhida deve ser ≥ 1.27.2.1 (a partir da qual o layout é ativado por padrão, seção 3.1 do PRD) e deve ser a mais recente disponível no momento da implementação, salvo motivo em contrário.

As ~10 dependências transitivas (`pymupdf`, `pymupdf-layout`, `onnxruntime` etc., seção 4 do PRD) não entram no `requirements.txt` — o pip as resolve automaticamente a partir de `pymupdf4llm`.

## 3. `converter.py` — estrutura de funções

Script único, sem módulos adicionais (proporcional ao escopo). Sem argumentos de linha de comando. Uso pretendido: **duplo clique direto em `converter.py`** no Windows Explorer — a associação padrão do Windows com `.py` abre um terminal e roda o script (premissa 4 do PRD, mesmo comportamento de outros scripts do Everton, ex. `mineracao_emails.py`). Rodar `python converter.py` num terminal já aberto continua funcionando como alternativa equivalente. Ao final da execução (resumo impresso ou qualquer um dos caminhos de saída sem conversão), o programa simplesmente termina — **sem pausa nem `input()` de "pressione Enter para fechar"**; a janela pode fechar sozinha, decisão explícita do Everton (diferente do que o menu interativo já exige: escolher um PDF/opção e responder sim/não mantêm a janela aberta durante essa etapa).

```
PASTA_A_CONVERTER = Path(__file__).resolve().parent / "a_converter"
LIMITE_CONTEUDO_VAZIO = 50   # caracteres, após strip() — ver seção 5.3

def listar_pdfs() -> list[Path]
def exibir_menu(pdfs: list[Path]) -> None
def obter_escolha(pdfs: list[Path]) -> str
def perguntar_sim_nao(pergunta: str) -> bool
def validar_abertura(pdf_path: Path) -> tuple[bool, str | None]
def converter_um(pdf_path: Path) -> dict
def imprimir_resumo(resultados: list[dict]) -> None
def main() -> None

if __name__ == "__main__":
    main()
```

### 3.1 `listar_pdfs()`
- Lista arquivos com extensão `.pdf` (case-insensitive: `.pdf`, `.PDF`, etc.) diretamente dentro de `a_converter/`, sem recursão em subpastas.
- Ordenação: alfabética (`sorted()`), para que a numeração do menu seja estável entre execuções.
- Se `a_converter/` não existir por algum motivo, cria a pasta vazia antes de listar (autocorreção silenciosa, sem erro).

### 3.2 `exibir_menu(pdfs)`
Se `pdfs` estiver vazio, imprime e encerra o programa (critério de aceitação 3 do PRD):
```
Nenhum PDF encontrado na pasta 'a_converter/'.
Coloque arquivos .pdf nela e rode o programa novamente.
```
Caso contrário, imprime:
```
=== Conversor PDF -> Markdown ===
PDFs encontrados em a_converter/:
  1. relatorio.pdf
  2. contrato.pdf
  3. edital.pdf

  0. Converter todos os PDFs listados acima
  Q. Sair sem converter nada
```

### 3.3 `obter_escolha(pdfs)`
- Prompt: `Escolha uma opção: `
- Aceita: número de 1 a len(pdfs) (um PDF específico), `0` (todos), `q`/`Q` (sair) — comparação case-insensitive para a letra.
- Entrada inválida (não numérica fora do intervalo, ou letra diferente de Q): reimprime
  `Opção inválida. Digite o número de um PDF da lista, 0 para converter todos, ou Q para sair.`
  e pede a entrada de novo (loop), sem encerrar o programa.

### 3.4 `perguntar_sim_nao(pergunta)`
- Usada apenas na confirmação de "converter todos" (não há confirmação de sobrescrita — PRD seção 3, item 3).
- Aceita (case-insensitive, sem acento): `s`, `sim`, `n`, `nao`, `não`. Qualquer outra entrada repete a pergunta.
- Texto exato da pergunta (critério de aceitação 2 do PRD): `Converter todos os {N} PDFs encontrados? (s/n): `

### 3.5 `validar_abertura(pdf_path)` — pré-checagem antes de converter
`pymupdf4llm` é construído sobre `pymupdf` (instalado como dependência transitiva — seção 4 do PRD), então o script importa `pymupdf` diretamente para fazer uma checagem rápida antes de chamar `to_markdown`, de forma a separar claramente os dois motivos de erro mais comuns (critérios de aceitação 5 e 6 do PRD):

```python
import pymupdf

def validar_abertura(pdf_path: Path) -> tuple[bool, str | None]:
    try:
        doc = pymupdf.open(pdf_path)
    except Exception:
        return False, "arquivo PDF corrompido ou inválido"
    try:
        if doc.needs_pass:
            return False, "protegido por senha"
        return True, None
    finally:
        doc.close()
```
- Retorno `(True, None)`: segue para conversão.
- Retorno `(False, motivo)`: arquivo é reportado como falha com esse motivo exato, sem chamar `pymupdf4llm.to_markdown` (evita gastar tempo processando um arquivo que já se sabe que vai falhar).

### 3.6 `converter_um(pdf_path)`
Fluxo:
1. Imprime `Convertendo {pdf_path.name}...`
2. Chama `validar_abertura`. Se falhar, retorna resultado de erro com o motivo da seção 3.5.
3. Chama `pymupdf4llm.to_markdown(str(pdf_path))` **sem nenhum parâmetro além do caminho** — comportamento padrão da biblioteca, layout ativado, sem chamar `use_layout(False)` (decisão não-negociável, PRD seção 3.1). Envolvido em `try/except Exception as e`; qualquer exceção não prevista aqui é capturada e reportada com `str(e)` como motivo, sem interromper o restante da execução (tratamento de erro por arquivo, PRD seção 7).
4. Se a conversão retornar texto: grava em `pdf_path.with_suffix(".md")` usando `open(..., "w", encoding="utf-8")` — grava e sobrescreve sem perguntar, é o comportamento padrão de `"w"` (critério de aceitação 4).
5. Verifica conteúdo vazio: `if len(texto.strip()) < LIMITE_CONTEUDO_VAZIO`. Se vazio/quase vazio, marca o resultado com aviso (ver 3.7 e critério de aceitação 7), mas ainda conta como sucesso (o arquivo `.md` foi gerado, só o conteúdo é pobre).
6. Retorna um dicionário:
```python
{
    "nome_pdf": pdf_path.name,
    "sucesso": bool,
    "erro": str | None,
    "aviso_vazio": bool,
}
```

### 3.7 Textos de terminal (exatos)
- Sucesso: `Concluído: {nome_md} gerado com sucesso.`
- Sucesso com aviso de conteúdo vazio: além da linha de sucesso, imprime
  `Aviso: o conteúdo de {nome_md} ficou vazio (ou quase vazio). Esse PDF pode ser uma digitalização sem texto pesquisável — não suportado nesta versão.`
- Erro: `Erro ao converter {nome_pdf}: {motivo}.`
  - `{motivo}` é um dos três valores fixos de `validar_abertura` (`"arquivo PDF corrompido ou inválido"`, `"protegido por senha"`) ou a mensagem crua da exceção capturada no passo 3 de `converter_um`.

### 3.8 `imprimir_resumo(resultados)`
Formato (critérios de aceitação 2, 5 e 6):
```
=== Resumo ===
Convertidos com sucesso: {sucesso}/{total}
Falharam: {falhas}/{total}

Falhas:
  - {nome_pdf}: {motivo}
  - ...

Avisos (conteúdo vazio ou quase vazio):
  - {nome_pdf}
  - ...
```
As seções "Falhas" e "Avisos" só são impressas se houver pelo menos um item.

### 3.9 `main()`
1. `pdfs = listar_pdfs()`
2. `exibir_menu(pdfs)` — se `pdfs` vazio, a própria função já encerra o fluxo (`sys.exit(0)` após a mensagem).
3. `escolha = obter_escolha(pdfs)`
4. Se `escolha == "Q"`: imprime `Nenhum arquivo foi convertido. Até logo!` e encerra.
5. Se `escolha == "0"`:
   - Pergunta confirmação (`perguntar_sim_nao`, texto da seção 3.4). Se "não": imprime `Nenhum arquivo foi convertido. Até logo!` e encerra.
   - Se "sim": chama `converter_um` para cada PDF da lista, na ordem de `listar_pdfs()`.
6. Se `escolha` for um número de 1 a N: chama `converter_um` apenas para o PDF correspondente.
7. Chama `imprimir_resumo(resultados)`.
8. Fim do programa — não há loop de volta ao menu (uma execução do script = uma sessão de conversão, conforme premissa 4 do PRD: `python converter.py` é rodado de novo sempre que o Everton quiser converter mais arquivos).

## 4. `a_converter/.gitkeep`
Arquivo vazio, único propósito é permitir versionar a pasta vazia (PRD seção 6).

## 5. `.gitignore`
```
# Ambiente virtual (se o Everton optar por usar um)
venv/
.venv/

# PDFs e Markdown que o Everton for colocando/gerando na pasta de trabalho
a_converter/*
!a_converter/.gitkeep
```
O PDF de exemplo (`PES_TEC_SOC_COMP_ACE_2021.pdf`) permanece na raiz, fora de `a_converter/`, então não é afetado por essa regra — quando movido para dentro de `a_converter/` para teste manual, passa a ser ignorado pelo Git, o que é o comportamento correto (é um dado de teste local, não deve virar commit).

## 6. `README.md` — conteúdo obrigatório (linguagem não-técnica)
1. O que a ferramenta faz, em 2-3 frases (reduzir tokens ao enviar PDFs para o Claude).
2. Pré-requisito: Python instalado (sem detalhar versão mínima com jargão — já confirmado compatível na máquina do Everton).
3. Passo a passo de instalação: `pip install -r requirements.txt`, com aviso explícito de que esse passo baixa cerca de 90 MB e pode levar alguns minutos na primeira vez (critério de aceitação 11 do PRD).
4. Passo a passo de uso: colocar PDFs em `a_converter/` e dar duplo clique em `converter.py` (abre um terminal com o menu). Alternativa para quem preferir: abrir um terminal na pasta do projeto e rodar `python converter.py`.
5. O que esperar: o `.md` aparece do lado do PDF, dentro de `a_converter/`; rodar de novo sobrescreve sem avisar. Assim que a conversão termina, a janela do terminal fecha sozinha (não é preciso apertar nada).
6. Nota sobre limitação: PDFs escaneados (sem texto pesquisável) e PDFs protegidos por senha não são suportados nesta versão.

## 7. Decisões técnicas desta Spec sem menção explícita no PRD
- Limite de "conteúdo vazio" fixado em 50 caracteres após `strip()` (seção 3.6). É um valor arbitrário desta Spec, documentado aqui para poder ser ajustado depois se, no teste manual com o PDF de exemplo, gerar falsos positivos/negativos.
- Pré-checagem de PDF via `pymupdf.open()` antes de chamar `pymupdf4llm.to_markdown()` (seção 3.5), para poder diferenciar "corrompido" de "protegido por senha" com mensagens específicas, já que `pymupdf4llm.to_markdown()` sozinho não expõe essa distinção de forma direta.
- Uma execução do script cobre uma única ação de conversão (um PDF ou todos) e depois encerra — não há loop de menu contínuo, para manter o script simples (premissa 5 do PRD).
- Execução via duplo clique é o uso pretendido principal (premissa 4 do PRD, revisada). O script não tem nenhuma linha de pausa (`input()`) no final — decisão explícita do Everton: assim que a conversão acaba, a janela pode fechar sozinha, sem precisar apertar Enter. O menu interativo (escolher PDF/opção, confirmar sim/não) já é o que mantém a janela aberta enquanto há algo para o Everton decidir.

## Plano de Execução

- [ ] Task 1 — Criar `a_converter/.gitkeep` e `.gitignore` conforme seções 4 e 5.
- [ ] Task 2 — Criar `requirements.txt` com `pymupdf4llm` pinado na versão mais recente disponível (confirmar versão exata no PyPI no momento da implementação).
- [ ] Task 3 — Implementar `listar_pdfs()` em `converter.py` e testar manualmente com a pasta `a_converter/` vazia e com PDFs de exemplo.
- [ ] Task 4 — Implementar `exibir_menu()`, `obter_escolha()` e `perguntar_sim_nao()`, e testar manualmente a navegação (entradas válidas e inválidas).
- [ ] Task 5 — Implementar `validar_abertura()` e testar com um PDF válido, um corrompido (ex. renomear um arquivo não-PDF para `.pdf`) e, se possível, um PDF protegido por senha.
- [ ] Task 6 — Implementar `converter_um()` (chamada a `pymupdf4llm.to_markdown()` com comportamento padrão, gravação do `.md`, verificação de conteúdo vazio) e testar com o PDF de exemplo `PES_TEC_SOC_COMP_ACE_2021.pdf` movido para `a_converter/`.
- [ ] Task 7 — Implementar `imprimir_resumo()` e `main()`, cobrindo os três fluxos (um PDF, todos os PDFs, pasta vazia/saída sem converter). Testar especificamente via duplo clique em `converter.py` (não só rodando pelo terminal), confirmando que o menu funciona normalmente e que a janela fecha sozinha ao final, sem pausa.
- [ ] Task 8 — Rodar manualmente os 11 critérios de aceitação do PRD (seção 12), incluindo o teste de reprodutibilidade da premissa 9 (converter o mesmo PDF duas vezes e comparar o `.md` gerado byte a byte).
- [ ] Task 9 — Escrever `README.md` conforme seção 6 desta Spec.
- [ ] Task 10 — Revisão final: confirmar que nenhum arquivo fora da pasta do projeto foi lido/criado/modificado, revisar `git status` e propor texto de commit ao Everton.

## Desvios

(vazio — a ser preenchido durante a implementação)
