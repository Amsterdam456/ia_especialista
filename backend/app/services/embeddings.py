import os
import pickle
import re
import unicodedata
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

EMBEDDINGS_FILE = settings.EMBEDDINGS_FILE

# Estrutura em memoria
emb_store: List[Dict] = []


# --------------------------
# HELPERS
# --------------------------

def reset_embeddings() -> None:
    """Limpa vetorizacoes em memoria e arquivo."""
    global emb_store
    emb_store = []

    if os.path.exists(EMBEDDINGS_FILE):
        os.remove(EMBEDDINGS_FILE)


def store_embeddings(text_chunks: List[Dict]) -> None:
    """
    Recebe uma lista de chunks no formato:
    {
        "text": "...",
        "source": "...",
        "page": 3,
        "order": 10
    }
    """
    global emb_store

    for item in text_chunks:
        text = (item.get("text") or "").strip()
        if not text:
            continue

        # Metadados semânticos leves (heurística) para melhorar qualidade do RAG.
        # Não depende de estrutura fixa do documento (contrato/política/etc).
        # Se o chunk já vier com metadados (ex.: do ingest), respeitamos;
        # caso contrário, inferimos por heurísticas.
        raw_source = str(item.get("source") or "")
        raw_page = int(item.get("page") or 0) or None
        inferred_category, inferred_role, inferred_topic, inferred_doc_type = build_semantic_metadata(
            text=text,
            source=raw_source,
            page=raw_page,
        )
        category = (item.get("category") or inferred_category) if isinstance(item.get("category"), str) else inferred_category
        role = (item.get("role") or inferred_role) if isinstance(item.get("role"), str) else inferred_role
        topic = (item.get("topic") or inferred_topic) if isinstance(item.get("topic"), str) else inferred_topic
        doc_type = inferred_doc_type

        semantic_text = build_semantic_embedding_text(
            text=text,
            source=str(item.get("source") or ""),
            page=int(item.get("page") or 0) or 0,
            category=category,
            role=role,
            topic=topic,
            doc_type=doc_type,
        )

        emb = model.encode(semantic_text, convert_to_numpy=True)

        emb_store.append(
            {
                "text": text,
                "semantic_text": semantic_text,
                "embedding": emb,
                "source": item.get("source"),
                "page": item.get("page"),
                "order": item.get("order"),
                "category": category,
                "role": role,
                "topic": topic,
                "doc_type": doc_type,
            }
        )

    save_embeddings()


def load_embeddings() -> None:
    """Carrega embeddings do disco."""
    global emb_store

    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, "rb") as f:
            emb_store = pickle.load(f)
    else:
        emb_store = []


def _ensure_loaded() -> None:
    if not emb_store:
        load_embeddings()


def _fold_to_ascii(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def _tokenize(text: str) -> set[str]:
    folded = _fold_to_ascii(text).lower().replace("_", " ").replace("-", " ")
    return {t for t in re.findall(r"[a-z0-9]+", folded) if t and t not in _QUERY_STOPWORDS}


def _infer_doc_type_from_source(source: str) -> str:
    s = _fold_to_ascii(source).lower()
    if s.startswith("ctt") or "contrato" in s:
        return "contrato"
    if s.startswith("pol") or "politica" in s:
        return "politica"
    if "manual" in s:
        return "manual"
    if "norma" in s or "normativo" in s:
        return "normativo"
    if "comunicado" in s:
        return "comunicado"
    if "regulamento" in s:
        return "regulamento"
    return "indefinido"


def _keyword_score(text: str, keywords: Tuple[str, ...]) -> int:
    folded = _fold_to_ascii(text).lower()
    return sum(1 for k in keywords if k in folded)


def _infer_category(text: str, source: str) -> str:
    # Leve e genérico: prioriza o vocabulário do trecho + nome do documento.
    s = f"{source}\n{text}"
    scores = {
        "financeiro": _keyword_score(
            s,
            (
                "r$",
                "valor",
                "pagamento",
                "taxa",
                "custo",
                "multa",
                "boleto",
                "fatura",
                "reembolso",
            ),
        ),
        "juridico": _keyword_score(
            s,
            (
                "contrato",
                "clausula",
                "cláusula",
                "rescisao",
                "rescisão",
                "foro",
                "vigencia",
                "vigência",
                "partes",
                "obrigacao",
                "obrigação",
            ),
        ),
        "operacional": _keyword_score(
            s,
            (
                "procedimento",
                "processo",
                "fluxo",
                "instru",
                "passo",
                "checklist",
                "operacao",
                "operação",
            ),
        ),
        "rh": _keyword_score(
            s,
            (
                "colaborador",
                "funcionario",
                "funcionário",
                "admissao",
                "admissão",
                "demissao",
                "demissão",
                "ferias",
                "férias",
                "beneficio",
                "benefício",
            ),
        ),
        "academico": _keyword_score(
            s,
            (
                "aluno",
                "matricula",
                "matrícula",
                "disciplina",
                "avaliacao",
                "avaliação",
                "campus",
                "prova",
            ),
        ),
        "institucional": _keyword_score(
            s,
            (
                "yduqs",
                "estacio",
                "estácio",
                "governanca",
                "governança",
                "diretoria",
                "comite",
                "comitê",
                "compliance",
                "codigo de conduta",
                "código de conduta",
            ),
        ),
    }
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else "indefinido"


def _infer_role(text: str) -> str:
    t = _fold_to_ascii(text).lower()
    if any(k in t for k in ("multa", "penal", "sanc", "sanção", "risco", "cobr")):
        return "risco"
    if any(k in t for k in ("devera", "deverá", "deve", "obrigat", "responsavel", "responsável", "cabera", "cabe")):
        return "obrigacao"
    if any(k in t for k in ("prazo", "dias", "data limite", "ate ", "até ")):
        return "prazo"
    if any(k in t for k in ("r$", "valor", "preco", "preço", "taxa", "custo", "pagamento")):
        return "valor"
    if any(k in t for k in ("define", "defin", "entende-se", "considera-se", "conceito")):
        return "definicao"
    if any(k in t for k in ("procedimento", "passo", "como", "orient", "instru")):
        return "procedimento"
    if any(k in t for k in ("proibido", "permitido", "nao pode", "não pode", "vedado", "regra")):
        return "regra"
    return "informacao"


def _infer_topic(text: str) -> str:
    t = _fold_to_ascii(text).lower()
    patterns = [
        ("data do evento", ("data do evento",)),
        ("horario do evento", ("horario:", "horário:", "das ", "as ", "às ")),
        ("local do evento", ("local:", "local ")),
        ("condicoes de pagamento", ("pagamento", "boleto", "fatura")),
        ("multas e penalidades", ("multa", "penal", "cobr")),
        ("prazos e comunicacoes", ("prazo", "dias", "antecedencia", "antecedência")),
        ("obrigacoes e responsabilidades", ("responsavel", "responsável", "cabe", "cabera", "devera", "deverá")),
    ]
    for topic, keys in patterns:
        if any(k in t for k in keys):
            return topic

    # Fallback simples: primeira frase curta
    first = re.split(r"[.\n;:]", text.strip(), maxsplit=1)[0].strip()
    first = re.sub(r"\s+", " ", first)
    return (first[:80] + "...") if len(first) > 80 else (first or "indefinido")


def build_semantic_metadata(text: str, source: str, page: int | None) -> tuple[str, str, str, str]:
    """
    Extrai metadados semânticos leves (heurística) para melhorar recuperação.
    Mantém compatibilidade: se não for possível inferir, retorna 'indefinido'.
    """
    doc_type = _infer_doc_type_from_source(source)
    category = _infer_category(text, source)
    role = _infer_role(text)
    topic = _infer_topic(text)
    return category, role, topic, doc_type


def build_semantic_embedding_text(
    *,
    text: str,
    source: str,
    page: int,
    category: str,
    role: str,
    topic: str,
    doc_type: str,
) -> str:
    """
    Constrói um texto "enriquecido" (conhecimento estruturado) para o embedding.

    Ideia: embeddings de texto cru tendem a misturar conceitos. Ao incluir categoria/papel/tópico,
    o vetor representa melhor "o que é" e "para que serve" o trecho, sem depender de um tipo de documento.
    """
    return "\n".join(
        [
            f"DOCUMENTO: {source or 'indefinido'}",
            f"TIPO_DOCUMENTO: {doc_type}",
            f"CATEGORIA: {category}",
            f"PAPEL: {role}",
            f"TOPICO: {topic}",
            f"PAGINA: {page}",
            "TEXTO:",
            text,
        ]
    ).strip()


def _summary_relevance_score(text: str) -> float:
    """
    Heuristica simples para resumos: prioriza campos-chave (data, horario, local, valores)
    e evita metadados (hash/assinaturas/ids).
    """
    t = _fold_to_ascii(text).lower()
    score = 1.0

    if "data do evento" in t:
        score += 6.0
    if "horario" in t or "horario:" in t or "hora" in t:
        score += 3.0
    if "duracao" in t or "duracao:" in t:
        score += 3.0
    if "local" in t or "local:" in t:
        score += 3.0
    if "evento" in t or "confraternizacao" in t:
        score += 2.0

    if "r$" in t or "valor" in t or "preco" in t or "taxa" in t:
        score += 4.0

    if "cnpj" in t or "contratante" in t or "contratada" in t:
        score += 2.0

    if "dias" in t or "prazo" in t or "multa" in t or "penal" in t or "cobr" in t:
        score += 2.0

    if "sha256" in t or "hash" in t or "clicksign" in t or "assinatura" in t or "documento numero" in t:
        score -= 6.0

    return max(score, 0.0)


def _all_chunks_for_sources(sources: list[str]) -> list[Dict]:
    """
    Retorna todos os chunks dos sources informados.
    Usado para resumo de documento quando o usuario pede "resumo do arquivo X".
    """
    _ensure_loaded()
    wanted = set(sources)
    chunks: list[Dict] = []
    for item in emb_store:
        if item.get("source") in wanted:
            text = item.get("text") or ""
            chunks.append(
                {
                    "text": text,
                    "source": item.get("source", ""),
                    "page": item.get("page", 0),
                    "order": item.get("order", 0),
                    "score": float(item.get("score") or 0.0) + _summary_relevance_score(text),
                    "category": item.get("category", "indefinido"),
                    "role": item.get("role", "indefinido"),
                    "topic": item.get("topic", "indefinido"),
                }
            )
    chunks.sort(key=lambda x: (x["source"], int(x["page"]), int(x.get("order") or 0)))
    return chunks


def save_embeddings() -> None:
    """Persiste o emb_store em disco."""
    os.makedirs(os.path.dirname(EMBEDDINGS_FILE) or "data", exist_ok=True)
    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(emb_store, f)


def remove_embeddings_for_source(source: str) -> None:
    """Remove embeddings de um documento especifico."""
    global emb_store
    if not emb_store:
        load_embeddings()
    emb_store = [item for item in emb_store if item.get("source") != source]
    save_embeddings()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def search_similar_documents(query: str, k: int = 5) -> List[Dict]:
    """Retorna os K chunks mais similares com metadados completos."""
    if not emb_store:
        load_embeddings()

    if not emb_store:
        return []

    query_semantic = build_query_semantic_text(query)
    query_emb = model.encode(query_semantic, convert_to_numpy=True)
    scored = []

    for item in emb_store:
        score = _cosine_similarity(query_emb, item["embedding"])

        scored.append(
            {
                "text": item.get("text", ""),
                "source": item.get("source", ""),
                "page": item.get("page", 0),
                "order": item.get("order", 0),
                "category": item.get("category", "indefinido"),
                "role": item.get("role", "indefinido"),
                "topic": item.get("topic", "indefinido"),
                "doc_type": item.get("doc_type", "indefinido"),
                "score": score,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _token_overlap_score(query: str, text: str) -> float:
    q_tokens = set(re.findall(r"\w+", query.lower()))
    t_tokens = set(re.findall(r"\w+", text.lower()))
    if not q_tokens or not t_tokens:
        return 0.0
    return len(q_tokens & t_tokens) / max(len(q_tokens), 1)


def _rerank_matches(query: str, matches: List[Dict]) -> List[Dict]:
    intent = infer_query_intent(query)
    reranked = []
    for item in matches:
        overlap = _token_overlap_score(query, item["text"])
        score = (0.85 * item["score"]) + (0.15 * overlap)

        # Multiplicadores leves por metadados (não é filtro rígido).
        if intent["roles"] and item.get("role") in intent["roles"]:
            score *= 1.15
        if intent["categories"] and item.get("category") in intent["categories"]:
            score *= 1.10
        if intent["doc_types"] and item.get("doc_type") in intent["doc_types"]:
            score *= 1.05

        reranked.append({**item, "score": score})
    reranked.sort(key=lambda x: x["score"], reverse=True)
    return reranked


_QUERY_STOPWORDS = {
    "a",
    "o",
    "os",
    "as",
    "um",
    "uma",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "para",
    "por",
    "com",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "e",
    "ou",
    "que",
    "qual",
    "quais",
    "arquivo",
    "documento",
    "pdf",
    "página",
    "pagina",
    # siglas de documentos (ctt/pol) sao uteis para identificar arquivos, entao nao entram aqui
    "athena",
    "resumo",
    "resuma",
    "resumir",
    "sintese",
    "sintetize",
    "detalhe",
    "detalhar",
    "detalhado",
    "detalhada",
}


def infer_query_intent(query: str) -> dict:
    """
    Inferência leve do "tipo de pergunta" para guiar o retrieval.
    Ex.: se perguntar sobre "riscos", damos um boost em chunks com role=risco.
    """
    q = _fold_to_ascii(query).lower()
    roles: set[str] = set()
    categories: set[str] = set()
    doc_types: set[str] = set()

    if any(k in q for k in ("risco", "multa", "penal", "san")):
        roles.add("risco")
    if any(k in q for k in ("obrig", "respons", "dever")):
        roles.add("obrigacao")
    if any(k in q for k in ("prazo", "dias", "data limite", "ate ", "até ")):
        roles.add("prazo")
    if any(k in q for k in ("valor", "pagamento", "taxa", "custo", "finance")):
        roles.add("valor")
        categories.add("financeiro")

    if "jurid" in q or "contrato" in q or "clausula" in q:
        categories.add("juridico")
        doc_types.add("contrato")
    if "operac" in q or "proced" in q or "passo" in q:
        categories.add("operacional")
    if "rh" in q or "colaborador" in q or "beneficio" in q:
        categories.add("rh")
    if "academ" in q or "aluno" in q or "matric" in q:
        categories.add("academico")
    if "institu" in q or "yduqs" in q or "estacio" in q:
        categories.add("institucional")

    if re.search(r"\bctt\b", q) is not None:
        doc_types.add("contrato")
    if re.search(r"\bpol\b", q) is not None:
        doc_types.add("politica")

    return {"roles": roles, "categories": categories, "doc_types": doc_types}


def build_query_semantic_text(query: str) -> str:
    """
    Enriquecimento leve do texto de consulta.
    Ajuda o embedding da pergunta a ficar mais "alinhado" com os embeddings semânticos dos chunks.
    """
    intent = infer_query_intent(query)
    tags = []
    if intent["roles"]:
        tags.append("PAPEL_DESEJADO: " + ", ".join(sorted(intent["roles"])))
    if intent["categories"]:
        tags.append("CATEGORIA_DESEJADA: " + ", ".join(sorted(intent["categories"])))
    if intent["doc_types"]:
        tags.append("TIPO_DOCUMENTO_DESEJADO: " + ", ".join(sorted(intent["doc_types"])))
    tag_block = "\n".join(tags)
    return (tag_block + "\nPERGUNTA:\n" + query).strip() if tag_block else query


def _pick_preferred_sources(query: str, matches: List[Dict]) -> list[str]:
    """
    Se o usuario mencionar um documento/arquivo no texto da pergunta, tenta priorizar
    trechos do(s) documento(s) correspondente(s), evitando misturar politicas diferentes.
    """
    folded_query = _fold_to_ascii(query).lower()
    looks_like_specific_doc = (
        ("arquivo" in folded_query)
        or ("documento" in folded_query)
        or (".pdf" in folded_query)
        or re.search(r"\bctt\b", folded_query) is not None
        or re.search(r"\bpol\b", folded_query) is not None
        or re.search(r"\bpol\W*\d", folded_query) is not None
    )
    if not looks_like_specific_doc:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    by_source: dict[str, list[dict]] = defaultdict(list)
    for m in matches:
        by_source[m["source"]].append(m)

    scored_sources: list[tuple[str, int, float]] = []
    for source, items in by_source.items():
        source_tokens = _tokenize(source)
        overlap = len(query_tokens & source_tokens)
        best_score = max((float(i.get("score") or 0.0) for i in items), default=0.0)
        scored_sources.append((source, overlap, best_score))

    scored_sources.sort(key=lambda x: (x[1], x[2]), reverse=True)
    if not scored_sources:
        return []

    best_source, best_overlap, best_score = scored_sources[0]

    # Heuristica: se houver pelo menos 1 token relevante em comum com o nome do arquivo,
    # assumimos que o usuario esta pedindo especificamente aquele documento.
    if best_overlap >= 1:
        # Inclui tambem outros sources empatados por overlap para permitir variantes do mesmo doc.
        preferred = [s for (s, ov, _) in scored_sources if ov == best_overlap and ov >= 1]
        return preferred[:3]

    # Fallback: se o melhor match for muito melhor que os demais, use somente ele.
    if best_score >= 0.60:
        return [best_source]

    return []


def get_relevant_chunks(query: str, k: int = 3, max_chars: int = 4000) -> str:
    """Retorna os melhores trechos formatados para o modelo, com limite de tamanho."""
    context, _ = get_relevant_chunks_with_meta(query, k=k, max_chars=max_chars)
    return context


def get_relevant_chunks_with_meta(
    query: str,
    k: int = 3,
    max_chars: int = 4000,
    max_per_source: int = 2,
    mode: str = "qa",
) -> tuple[str, list[dict]]:
    """Retorna contexto formatado e metadados para citacoes."""
    # Para "summary", buscamos mais candidatos para aumentar cobertura do documento.
    candidates = max(k * 6, 12) if mode != "summary" else max(k * 10, 40)
    matches = search_similar_documents(query, candidates)
    matches = _rerank_matches(query, matches)

    if not matches:
        return "", []

    preferred_sources = _pick_preferred_sources(query, matches)
    if preferred_sources:
        if mode == "summary":
            # Para resumo de um documento especifico, preferimos cobertura do PDF inteiro,
            # e nao apenas os top-K semanticamente similares a uma pergunta generica.
            matches = _all_chunks_for_sources(preferred_sources)
            max_per_source = max(max_per_source, 50)
        else:
            matches = [m for m in matches if m.get("source") in preferred_sources]
            # Quando um documento especifico foi identificado, permite mais trechos dele.
            max_per_source = max(max_per_source, 4)

    def iter_selected() -> list[Dict]:
        if mode != "summary":
            return matches

        # Seleção mais diversa: tenta cobrir mais páginas e reduzir redundância.
        per_page_best: dict[tuple[str, int], Dict] = {}
        for m in matches:
            key = (m["source"], int(m["page"]))
            if key not in per_page_best or m["score"] > per_page_best[key]["score"]:
                per_page_best[key] = m

        diverse = list(per_page_best.values())

        # No resumo, limitamos a quantidade de páginas para evitar estourar o contexto do modelo.
        diverse.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
        selected: list[Dict] = []

        # Garante a primeira página (geralmente tem dados-chave: data/local/partes).
        page1 = next((d for d in diverse if int(d.get("page") or 0) == 1), None)
        if page1:
            selected.append(page1)

        for d in diverse:
            if page1 and d is page1:
                continue
            selected.append(d)
            if len(selected) >= 8:
                break

        selected.sort(key=lambda x: (x.get("source", ""), int(x.get("page") or 0), int(x.get("order") or 0)))

        # Preenche com os demais melhores para complementar.
        remaining = [m for m in matches if (m["source"], int(m["page"])) not in per_page_best]
        remaining.sort(key=lambda x: (x["source"], int(x["page"]), int(x.get("order") or 0)))
        return selected + remaining

    formatted: list[str] = []
    total_chars = 0
    citations: list[dict] = []
    seen = set()
    per_source = defaultdict(int)
    for m in iter_selected():
        normalized = _normalize_text(m["text"])
        if normalized in seen:
            continue
        if per_source[m["source"]] >= max_per_source:
            continue
        header_parts = [f"Documento: {m['source']}", f"Pagina {m['page']}"]
        cat = m.get("category")
        role = m.get("role")
        topic = m.get("topic")
        if cat and cat != "indefinido":
            header_parts.append(f"Categoria {cat}")
        if role and role != "indefinido":
            header_parts.append(f"Papel {role}")
        if topic and topic != "indefinido":
            header_parts.append(f"Topico {topic}")
        header = " | ".join(header_parts)
        snippet = f"[{header}] Trecho:\n{m['text']}"
        total_chars += len(snippet)
        formatted.append(snippet)
        citations.append({"source": m["source"], "page": m["page"], "score": m["score"]})
        seen.add(normalized)
        per_source[m["source"]] += 1
        if total_chars >= max_chars:
            break

    return "\n\n".join(formatted), citations
