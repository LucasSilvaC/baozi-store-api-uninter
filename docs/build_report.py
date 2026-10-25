from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Flowable,
)


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "postman" / "capturas"
LOGO_PATH = ROOT / "docs" / "assets" / "uninter_logo.jpeg"
INPUT_DATA = ROOT / "dados.txt"
REPOSITORY_URL_FILE = ROOT / "entrega" / "repositorio.txt"
DEFAULT_OUTPUT = ROOT / "entrega" / "Trabalho_Atividade_Praticas_Baozi_Store.pdf"
NEWMAN_RESULTS_FILE = ROOT / "entrega" / "newman-results.json"
POSTMAN_CAPTURES = [
    ("01-post-cliente.jpg", "POST /api/clientes - 201 Created"),
    ("02-post-produto.jpg", "POST /api/produtos - 201 Created"),
    ("03-post-pedido.jpg", "POST /api/pedidos - 201 Created"),
    ("04-get-clientes.jpg", "GET /api/clientes - 200 OK"),
    ("05-get-produtos.jpg", "GET /api/produtos - 200 OK"),
    ("06-get-pedidos.jpg", "GET /api/pedidos - 200 OK"),
    ("07-get-cliente-id.jpg", "GET /api/clientes/{id} - 200 OK"),
    ("08-get-produto-id.jpg", "GET /api/produtos/{id} - 200 OK"),
    ("09-get-pedido-id.jpg", "GET /api/pedidos/{id} - 200 OK"),
    ("10-delete-pedido.jpg", "DELETE /api/pedidos/{id} - 204 No Content"),
    ("11-delete-produto.jpg", "DELETE /api/produtos/{id} - 204 No Content"),
    ("12-delete-cliente.jpg", "DELETE /api/clientes/{id} - 204 No Content"),
]


def student_details() -> tuple[str, str]:
    text = INPUT_DATA.read_text(encoding="utf-8-sig")
    name_match = re.search(r"^\s*Nome\s*:\s*(.+?)\s*$", text, re.MULTILINE | re.IGNORECASE)
    ru_match = re.search(r"^\s*RU\s*:\s*(.+?)\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not name_match or not ru_match:
        raise ValueError("Não foi possível ler Nome e RU de dados.txt.")
    return name_match.group(1), ru_match.group(1)


def repository_url() -> str:
    if not REPOSITORY_URL_FILE.exists():
        raise FileNotFoundError(
            f"Crie {REPOSITORY_URL_FILE.relative_to(ROOT)} e coloque nele a URL do repositório."
        )
    url = REPOSITORY_URL_FILE.read_text(encoding="utf-8-sig").strip()
    if not url.startswith(("https://", "http://")):
        raise ValueError("A URL do repositório precisa começar com https:// ou http://.")
    return url


def read_newman_results() -> tuple[dict, list[dict]]:
    if not NEWMAN_RESULTS_FILE.exists():
        raise FileNotFoundError(
            "Gere entrega/newman-results.json executando a coleção Postman com Newman e o reporter JSON."
        )
    report = json.loads(NEWMAN_RESULTS_FILE.read_text(encoding="utf-8"))
    run = report.get("run", {})
    request_stats = run.get("stats", {}).get("requests", {})
    assertion_stats = run.get("stats", {}).get("assertions", {})
    executions = []
    for execution in run.get("executions", []):
        response = execution.get("response") or {}
        stream = response.get("stream") or {}
        if isinstance(stream, dict) and stream.get("type") == "Buffer":
            body_text = bytes(stream.get("data", [])).decode("utf-8", errors="replace")
        else:
            body_text = ""
        try:
            response_body = json.loads(body_text) if body_text else None
        except json.JSONDecodeError:
            response_body = {"texto": body_text}

        request = execution.get("request", {})
        url = request.get("url", {})
        path = url.get("path") or []
        route = "/" + "/".join(str(part) for part in path)
        method = request.get("method", "")
        request_body = None
        if method in {"POST", "PUT"} and isinstance(response_body, dict):
            request_body = {key: value for key, value in response_body.items() if key != "id"}

        executions.append({
            "name": execution.get("item", {}).get("name", "Requisição"),
            "method": method,
            "route": route,
            "status": response.get("code"),
            "statusText": response.get("status", ""),
            "responseTimeMs": response.get("responseTime", 0),
            "requestBody": request_body,
            "responseBody": response_body,
        })

    summary = {
        "requestCount": request_stats.get("total", len(executions)),
        "failedCount": request_stats.get("failed", len(run.get("failures", []))),
        "assertionCount": assertion_stats.get("total", 0),
        "assertionFailedCount": assertion_stats.get("failed", 0),
        "durationMs": run.get("timings", {}).get("completed", 0) - run.get("timings", {}).get("started", 0),
    }
    if summary["failedCount"] or summary["assertionFailedCount"]:
        raise ValueError(
            "Newman registrou "
            f"{summary['failedCount']} falhas de requisição e "
            f"{summary['assertionFailedCount']} falhas de verificação."
        )
    if not executions:
        raise ValueError("O arquivo Newman não contém requisições executadas.")
    return summary, executions


def read_postman_captures() -> list[tuple[Path, str]]:
    captures = []
    for filename, caption in POSTMAN_CAPTURES:
        path = CAPTURE_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"Captura obrigatória do Postman não encontrada: {path}.")
        image = Image(str(path))
        if image.imageWidth < 700 or image.imageHeight < 700:
            raise ValueError(f"A captura do Postman está abaixo da resolução esperada: {path}.")
        captures.append((path, caption))
    return captures


class UseCaseDiagram(Flowable):
    """Diagrama UML vetorial com um ator e uma fronteira para a API."""

    entities = {
        "Cliente": [
            "Cadastrar cliente",
            "Listar clientes",
            "Consultar cliente por ID",
            "Atualizar cliente",
            "Excluir cliente",
        ],
        "Produto": [
            "Cadastrar produto",
            "Listar produtos",
            "Consultar produto por ID",
            "Atualizar produto",
            "Excluir produto",
        ],
        "Pedido": [
            "Cadastrar pedido",
            "Listar pedidos",
            "Consultar pedido por ID",
            "Atualizar pedido",
            "Excluir pedido",
        ],
    }

    def __init__(self, height: float = 374):
        super().__init__()
        self.height = height

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self.width = available_width
        return available_width, self.height

    def draw(self) -> None:
        canvas = self.canv
        canvas.saveState()
        boundary_x = 105
        boundary_y = 8
        boundary_width = self.width - boundary_x - 4
        boundary_height = self.height - 16
        boundary_top = boundary_y + boundary_height
        actor_x = 43
        actor_center_y = self.height / 2
        ellipse_x = boundary_x + 22
        ellipse_width = min(270, boundary_width - 34)

        canvas.setStrokeColor(colors.HexColor("#7C8794"))
        canvas.setLineWidth(0.9)
        canvas.roundRect(boundary_x, boundary_y, boundary_width, boundary_height, 7, stroke=1, fill=0)
        canvas.setFillColor(colors.HexColor("#2D526B"))
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(boundary_x + 10, boundary_top - 15, "Baozi Store API")

        cases = []
        cursor_y = boundary_top - 29
        for entity, use_cases in self.entities.items():
            canvas.setFillColor(colors.HexColor("#39434D"))
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(boundary_x + 12, cursor_y, entity)
            cursor_y -= 12
            for label in use_cases:
                cases.append((label, cursor_y - 7))
                cursor_y -= 17
            cursor_y -= 2

        for _, center_y in cases:
            canvas.setStrokeColor(colors.HexColor("#9AA4AF"))
            canvas.setLineWidth(0.55)
            canvas.line(actor_x + 21, actor_center_y, ellipse_x, center_y)

        canvas.setStrokeColor(colors.HexColor("#202830"))
        canvas.setLineWidth(1.2)
        head_y = actor_center_y + 16
        canvas.circle(actor_x, head_y, 5, stroke=1, fill=0)
        canvas.line(actor_x, head_y - 5, actor_x, actor_center_y - 6)
        canvas.line(actor_x - 10, actor_center_y + 5, actor_x + 10, actor_center_y + 5)
        canvas.line(actor_x, actor_center_y - 6, actor_x - 9, actor_center_y - 19)
        canvas.line(actor_x, actor_center_y - 6, actor_x + 9, actor_center_y - 19)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#303943"))
        canvas.drawCentredString(actor_x, actor_center_y - 31, "Usuário da API")

        for label, center_y in cases:
            canvas.setStrokeColor(colors.HexColor("#365F78"))
            canvas.setFillColor(colors.white)
            canvas.ellipse(ellipse_x, center_y - 7, ellipse_x + ellipse_width, center_y + 7, stroke=1, fill=1)
            canvas.setFillColor(colors.HexColor("#202830"))
            canvas.setFont("Helvetica", 7.6)
            canvas.drawCentredString(ellipse_x + ellipse_width / 2, center_y - 2.6, label)
        canvas.restoreState()


def build_styles():
    base = getSampleStyleSheet()
    return {
        "institution": ParagraphStyle(
            "Institution", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=12,
            leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#202830"), spaceAfter=3
        ),
        "school": ParagraphStyle(
            "School", parent=base["Normal"], fontName="Helvetica", fontSize=10,
            leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#353D46")
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=19,
            leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#202830"), spaceAfter=8
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=14,
            leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#2D526B")
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta", parent=base["Normal"], fontName="Helvetica", fontSize=11,
            leading=17, alignment=TA_CENTER, textColor=colors.HexColor("#303943")
        ),
        "h1": ParagraphStyle(
            "SectionHeading", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14,
            leading=18, textColor=colors.HexColor("#202830"), spaceBefore=11, spaceAfter=6,
            keepWithNext=True
        ),
        "h2": ParagraphStyle(
            "SubHeading", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11,
            leading=14, textColor=colors.HexColor("#2D526B"), spaceBefore=8, spaceAfter=4,
            keepWithNext=True
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.7,
            leading=14, alignment=TA_JUSTIFY, textColor=colors.HexColor("#202830"), spaceAfter=6
        ),
        "body_left": ParagraphStyle(
            "BodyLeft", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5,
            leading=13, alignment=TA_LEFT, textColor=colors.HexColor("#202830"), spaceAfter=4
        ),
        "caption": ParagraphStyle(
            "Caption", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=8.3,
            leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#59636E"), spaceBefore=3, spaceAfter=8
        ),
        "table": ParagraphStyle(
            "TableText", parent=base["Normal"], fontName="Helvetica", fontSize=8.1,
            leading=10.4, textColor=colors.HexColor("#202830")
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8.2,
            leading=10.4, textColor=colors.HexColor("#202830")
        ),
        "code": ParagraphStyle(
            "Code", parent=base["Code"], fontName="Courier", fontSize=7.7,
            leading=10.4, leftIndent=0, rightIndent=0, spaceAfter=0
        ),
    }


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def add_table(story: list, rows: list[list[str]], widths: list[float], styles, repeat_rows: int = 1):
    converted = []
    for row_index, row in enumerate(rows):
        row_style = styles["table_header"] if row_index < repeat_rows else styles["table"]
        converted.append([Paragraph(cell, row_style) for cell in row])
    table = Table(converted, colWidths=widths, repeatRows=repeat_rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, repeat_rows - 1), colors.HexColor("#E9EDF1")),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#BCC5CE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, repeat_rows), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 7))


def add_code_block(story: list, code: str, styles, width: float):
    code_para = Paragraph(code.replace("\n", "<br/>"), styles["code"])
    table = Table([[code_para]], colWidths=[width], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCD3DA")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))


def header_footer(canvas, document):
    if document.page == 1:
        return
    canvas.saveState()
    page_width, page_height = A4
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#69737D"))
    canvas.drawString(document.leftMargin, page_height - 40, "DESENVOLVIMENTO WEB BACK-END  |  ATIVIDADE PRÁTICA")
    canvas.drawRightString(page_width - document.rightMargin, 31, f"Página {document.page - 1}")
    canvas.restoreState()


def build_pdf(output_path: Path) -> None:
    name, ru = student_details()
    repo = repository_url()
    run_summary, executions = read_newman_results()
    postman_captures = read_postman_captures()
    if not LOGO_PATH.exists():
        raise FileNotFoundError(f"Logo do modelo não encontrado em {LOGO_PATH}.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = A4
    left_margin = 19 * mm
    right_margin = 19 * mm
    top_margin = 24 * mm
    bottom_margin = 21 * mm
    usable_width = page_width - left_margin - right_margin
    styles = build_styles()
    story = []

    logo = Image(str(LOGO_PATH))
    logo.drawWidth = 39 * mm
    logo.drawHeight = logo.drawWidth * logo.imageHeight / logo.imageWidth
    logo.hAlign = "CENTER"
    story.extend([
        Spacer(1, 18 * mm),
        logo,
        Spacer(1, 9 * mm),
        para("CENTRO UNIVERSITÁRIO INTERNACIONAL UNINTER", styles["institution"]),
        para("ESCOLA SUPERIOR POLITÉCNICA", styles["school"]),
        Spacer(1, 2 * mm),
        para("DESENVOLVIMENTO WEB BACK-END", styles["school"]),
        Spacer(1, 33 * mm),
        para("ATIVIDADE PRÁTICA", styles["cover_title"]),
        para("API REST BAOZI STORE", styles["cover_subtitle"]),
        Spacer(1, 42 * mm),
        para(f"{name} - RU: {ru}", styles["cover_meta"]),
        Spacer(1, 6 * mm),
        para("Monte Mor - SP", styles["cover_meta"]),
        Spacer(1, 4 * mm),
        para("2026", styles["cover_meta"]),
        PageBreak(),
    ])

    story.extend([
        para("ATIVIDADE PRÁTICA", styles["h1"]),
        para("API REST para a Baozi Store", styles["h2"]),
        para(
            "Este trabalho apresenta uma API REST para apoiar o controle de clientes, produtos e pedidos de uma pequena loja de pão chinês. A implementação usa entidades JPA, banco relacional H2 e endpoints JSON organizados no padrão MVC do Spring.",
            styles["body"],
        ),
        para("1. Situação fictícia", styles["h1"]),
        para(
            f"A Baozi Store é uma loja fictícia que vende pão chinês por unidade. Para organizar as vendas, foi criada uma API que registra clientes, produtos e pedidos. O cenário de demonstração utiliza <b>{name} (RU: {ru})</b>, cadastrado como cliente. O produto é o baozi tradicional de carne, vendido por R$ 8,50 a unidade e com estoque disponível. Em 25 de outubro de 2026, o cliente solicita três unidades. O pedido registra o cliente, o produto e a quantidade solicitada.",
            styles["body"],
        ),
        para(
            "O atributo <i>estoque</i> segue o tipo Boolean sugerido no enunciado e indica disponibilidade (true ou false). Como o modelo não define uma quantidade numérica em estoque, o sistema não calcula saldo de unidades.",
            styles["body"],
        ),
        para("2. Diagrama de caso de uso", styles["h1"]),
        para(
            "O ator Usuário da API interage com as operações de criação, listagem, consulta por ID, atualização e exclusão de cada entidade.",
            styles["body"],
        ),
        UseCaseDiagram(),
        para("Figura 1 - Diagrama UML de caso de uso da API Baozi Store.", styles["caption"]),
        PageBreak(),
        para("3. Especificação da API", styles["h1"]),
        para(
            "A aplicação foi implementada em Java 17 com Spring Boot 4.1.2, Spring MVC, Spring Data JPA e H2. Os controladores recebem e retornam JSON; os repositórios JPA persistem as entidades em tabelas relacionais. O relacionamento de Pedido com Cliente e Produto é mapeado com chaves estrangeiras.",
            styles["body"],
        ),
        para("3.1 Entidades e campos", styles["h2"]),
    ])

    add_table(story, [
        ["Entidade", "Campo", "Tipo e descrição"],
        ["Cliente", "id", "Long - chave primária gerada automaticamente."],
        ["", "nome", "String - nome do cliente; obrigatório."],
        ["", "clienteDesde", "LocalDate - data de cadastro; preenchida automaticamente quando omitida."],
        ["Produto", "id", "Long - chave primária gerada automaticamente."],
        ["", "nome", "String - nome do produto; obrigatório."],
        ["", "preco", "BigDecimal - preço unitário, maior que zero."],
        ["", "estoque", "Boolean - indica se há produto disponível."],
        ["Pedido", "id", "Long - chave primária gerada automaticamente."],
        ["", "cliente", "Cliente - associação JPA ManyToOne; persiste cliente_id como chave estrangeira."],
        ["", "produto", "Produto - associação JPA ManyToOne; persiste produto_id como chave estrangeira."],
        ["", "quantidade", "Integer - quantidade pedida; deve ser positiva."],
    ], [74, 93, usable_width - 167], styles)

    story.extend([
        para(
            "No JSON do pedido, as associações são representadas por <i>clienteId</i> e <i>produtoId</i>. A entidade JPA mantém as referências a Cliente e Produto e grava as chaves estrangeiras no banco relacional.",
            styles["body"],
        ),
        para("3.2 Endpoints implementados", styles["h2"]),
        para(
            "Cada entidade implementa POST, GET geral, GET por ID e DELETE por ID. O PUT também foi incluído para completar o CRUD. Os endpoints aceitam e retornam JSON.",
            styles["body"],
        ),
    ])
    endpoint_rows = [["Método e rota", "Operação", "Resposta de sucesso"]]
    for resource, label, path in [
        ("Cliente", "cliente", "/api/clientes"),
        ("Produto", "produto", "/api/produtos"),
        ("Pedido", "pedido", "/api/pedidos"),
    ]:
        endpoint_rows.extend([
            [f"POST {path}", f"Criar {label}", "201 Created"],
            [f"GET {path}", f"Listar {label}s", "200 OK"],
            [f"GET {path}/{{id}}", f"Consultar {label} por ID", "200 OK"],
            [f"PUT {path}/{{id}}", f"Atualizar {label}", "200 OK"],
            [f"DELETE {path}/{{id}}", f"Excluir {label}", "204 No Content"],
        ])
    add_table(story, endpoint_rows, [201, 170, usable_width - 371], styles)
    story.extend([
        para("3.3 Regras de negócio", styles["h2"]),
        para(
            "O cadastro valida campos obrigatórios, preço positivo e quantidade positiva. Para registrar um pedido, a API exige que o cliente e o produto existam e que o produto esteja disponível. Consultas de IDs inexistentes retornam 404 Not Found; dados inválidos retornam 400 Bad Request. A exclusão respeita as chaves estrangeiras: o pedido deve ser removido antes do cliente ou do produto.",
            styles["body"],
        ),
        para("Exemplo de criação de pedido", styles["h2"]),
    ])
    story.append(para("Requisição POST /api/pedidos", styles["body_left"]))
    add_code_block(story, "{<br/>  &quot;clienteId&quot;: 1,<br/>  &quot;produtoId&quot;: 1,<br/>  &quot;quantidade&quot;: 3<br/>}", styles, usable_width)
    story.append(para("Resposta 201 Created", styles["body_left"]))
    add_code_block(story, "{<br/>  &quot;id&quot;: 1,<br/>  &quot;clienteId&quot;: 1,<br/>  &quot;produtoId&quot;: 1,<br/>  &quot;quantidade&quot;: 3<br/>}", styles, usable_width)

    story.extend([
        PageBreak(),
        para("4. Evidências de execução da coleção Postman", styles["h1"]),
        para(
            f"A coleção foi executada localmente com Newman 6.2.3, o executor de coleções Postman por linha de comando. Foram concluídas {run_summary['requestCount']} requisições e {run_summary['assertionCount']} verificações, sem falhas, em {run_summary['durationMs']} ms. A tabela registra os métodos, rotas, status HTTP e tempos medidos.",
            styles["body"],
        ),
    ])
    execution_rows = [["Requisição", "Método", "Rota", "Status", "ms"]]
    for execution in executions:
        execution_rows.append([
            execution["name"],
            execution["method"],
            execution["route"],
            f"{execution['status']} {execution['statusText']}",
            str(execution["responseTimeMs"]),
        ])
    add_table(story, execution_rows, [150, 48, 166, 76, usable_width - 440], styles)

    for execution in executions:
        if execution["method"] != "POST" or not isinstance(execution["responseBody"], dict):
            continue
        story.append(para(f"{execution['name']} - {execution['status']} {execution['statusText']}", styles["h2"]))
        if execution["requestBody"] is not None:
            story.append(para("JSON enviado", styles["body_left"]))
            request_json = json.dumps(execution["requestBody"], ensure_ascii=False, indent=2)
            add_code_block(story, request_json.replace("\n", "<br/>"), styles, usable_width)
        story.append(para("JSON retornado pela API", styles["body_left"]))
        response_json = json.dumps(execution["responseBody"], ensure_ascii=False, indent=2)
        add_code_block(story, response_json.replace("\n", "<br/>"), styles, usable_width)

    story.extend([
        PageBreak(),
        para("4.1 Capturas das 12 requisições no Postman Web", styles["h1"]),
        para(
            "As capturas mostram cada resposta individual da interface do Postman: criação, listagem, consulta por ID e exclusão de cliente, produto e pedido.",
            styles["body"],
        ),
    ])
    max_capture_height = page_height - top_margin - bottom_margin - 45 * mm
    for index, (capture_path, caption) in enumerate(postman_captures):
        if index:
            story.append(PageBreak())
        capture_image = Image(str(capture_path))
        scale = min(
            usable_width / capture_image.imageWidth,
            max_capture_height / capture_image.imageHeight,
        )
        capture_image.drawWidth = capture_image.imageWidth * scale
        capture_image.drawHeight = capture_image.imageHeight * scale
        capture_image.hAlign = "CENTER"
        story.append(capture_image)
        story.append(para(f"Figura {index + 2} - {caption}.", styles["caption"]))

    story.extend([
        para("5. Repositório do projeto", styles["h1"]),
        para("Endereço do repositório informado:", styles["body"]),
        para(f'<link href="{repo}" color="#2D526B">{repo}</link>', styles["body_left"]),
    ])

    document = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=left_margin, rightMargin=right_margin,
        topMargin=top_margin, bottomMargin=bottom_margin,
        title="Atividade Prática - API REST Baozi Store",
        author=f"{name} - RU {ru}",
        subject="Desenvolvimento Web Back-End",
    )
    document.build(story, onFirstPage=header_footer, onLaterPages=header_footer)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o PDF da atividade prática Baozi Store.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_pdf(args.output.resolve())
    print(f"PDF criado: {args.output.resolve()}")


if __name__ == "__main__":
    main()
