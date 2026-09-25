import os
import sys
from pathlib import Path

import pymupdf
import pymupdf4llm

try:
    from pymupdf4llm.ocr import rapidocr_onnx_backend as _rapidocr_backend

    def _full_ocr_sem_crash(img):
        # Contorno para bug do pymupdf4llm 1.28.2: quando o RapidOCR nao
        # encontra nenhum texto numa pagina, o engine retorna results=None
        # e a funcao original do pymupdf4llm quebra ao tentar iterar sobre
        # None. Tratamos esse caso como "nenhum texto encontrado" (lista
        # vazia), igual ao que ja acontece quando ha poucos resultados.
        engine = _rapidocr_backend.init_engine()
        resultados, _tempos = engine(img)
        if not resultados:
            return []
        return [(box, texto, float(score)) for box, texto, score in resultados]

    _rapidocr_backend.full_ocr = _full_ocr_sem_crash
except ImportError:
    pass

if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

PASTA_A_CONVERTER = Path(__file__).resolve().parent / "a_converter"
LIMITE_CONTEUDO_VAZIO = 50


def listar_pdfs() -> list[Path]:
    PASTA_A_CONVERTER.mkdir(exist_ok=True)
    pdfs = [
        p for p in PASTA_A_CONVERTER.iterdir()
        if p.is_file() and p.suffix.lower() == ".pdf"
    ]
    return sorted(pdfs)


def exibir_menu(pdfs: list[Path]) -> None:
    if not pdfs:
        print("Nenhum PDF encontrado na pasta 'a_converter/'.")
        print("Coloque arquivos .pdf nela e rode o programa novamente.")
        sys.exit(0)

    print("=== Conversor PDF -> Markdown ===")
    print("PDFs encontrados em a_converter/:")
    for i, pdf in enumerate(pdfs, start=1):
        print(f"  {i}. {pdf.name}")
    print()
    print("  0. Converter todos os PDFs listados acima")
    print("  Q. Sair sem converter nada")


def obter_escolha(pdfs: list[Path]) -> str:
    while True:
        escolha = input("Escolha uma opção: ").strip()

        if escolha.upper() == "Q":
            return "Q"
        if escolha == "0":
            return "0"
        if escolha.isdigit() and 1 <= int(escolha) <= len(pdfs):
            return escolha

        print("Opção inválida. Digite o número de um PDF da lista, 0 para converter todos, ou Q para sair.")


def perguntar_sim_nao(pergunta: str) -> bool:
    respostas_sim = {"s", "sim"}
    respostas_nao = {"n", "nao", "não"}
    while True:
        resposta = input(pergunta).strip().lower()
        if resposta in respostas_sim:
            return True
        if resposta in respostas_nao:
            return False


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


def converter_um(pdf_path: Path) -> dict:
    print(f"Convertendo {pdf_path.name}...")

    aberto, motivo = validar_abertura(pdf_path)
    if not aberto:
        print(f"Erro ao converter {pdf_path.name}: {motivo}.")
        return {"nome_pdf": pdf_path.name, "sucesso": False, "erro": motivo, "aviso_vazio": False}

    try:
        texto = pymupdf4llm.to_markdown(str(pdf_path))
    except Exception as e:
        motivo = str(e)
        print(f"Erro ao converter {pdf_path.name}: {motivo}.")
        return {"nome_pdf": pdf_path.name, "sucesso": False, "erro": motivo, "aviso_vazio": False}

    md_path = pdf_path.with_suffix(".md")
    with open(md_path, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)

    aviso_vazio = len(texto.strip()) < LIMITE_CONTEUDO_VAZIO
    print(f"Concluído: {md_path.name} gerado com sucesso.")
    if aviso_vazio:
        print(
            f"Aviso: o conteúdo de {md_path.name} ficou vazio (ou quase vazio). "
            "Esse PDF pode ser uma digitalização sem texto pesquisável — não suportado nesta versão."
        )

    return {"nome_pdf": pdf_path.name, "sucesso": True, "erro": None, "aviso_vazio": aviso_vazio}


def imprimir_resumo(resultados: list[dict]) -> None:
    total = len(resultados)
    sucesso = sum(1 for r in resultados if r["sucesso"])
    falhas = [r for r in resultados if not r["sucesso"]]
    avisos = [r for r in resultados if r["sucesso"] and r["aviso_vazio"]]

    print()
    print("=== Resumo ===")
    print(f"Convertidos com sucesso: {sucesso}/{total}")
    print(f"Falharam: {len(falhas)}/{total}")

    if falhas:
        print()
        print("Falhas:")
        for r in falhas:
            print(f"  - {r['nome_pdf']}: {r['erro']}")

    if avisos:
        print()
        print("Avisos (conteúdo vazio ou quase vazio):")
        for r in avisos:
            print(f"  - {r['nome_pdf']}")


def main() -> None:
    pdfs = listar_pdfs()
    exibir_menu(pdfs)

    escolha = obter_escolha(pdfs)

    if escolha.upper() == "Q":
        print("Nenhum arquivo foi convertido. Até logo!")
        return

    resultados = []

    if escolha == "0":
        if not perguntar_sim_nao(f"Converter todos os {len(pdfs)} PDFs encontrados? (s/n): "):
            print("Nenhum arquivo foi convertido. Até logo!")
            return
        for pdf in pdfs:
            resultados.append(converter_um(pdf))
    else:
        resultados.append(converter_um(pdfs[int(escolha) - 1]))

    imprimir_resumo(resultados)


if __name__ == "__main__":
    main()
