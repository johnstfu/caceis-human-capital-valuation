"""
chunker.py — Découpe les documents en chunks de 400 tokens
avec 50 tokens de chevauchement (overlap).

Utilise tiktoken cl100k_base (même encodage que GPT-4 / Claude).
"""

import re
import logging
from typing import List

import tiktoken

log = logging.getLogger(__name__)

CHUNK_SIZE    = 400   # tokens max par chunk
CHUNK_OVERLAP = 50    # tokens de chevauchement entre chunks


def _get_encoder():
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception as e:
        log.error(f"tiktoken init error: {e}")
        raise


def _clean_text(text: str) -> str:
    """Nettoie le texte extrait : espaces multiples, lignes vides excessives."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(\|[ ]*){3,}", "| ", text)  # tables xlsx trop denses
    return text.strip()


def chunk_document(doc: dict, encoder=None) -> List[dict]:
    """
    Découpe un document en chunks de CHUNK_SIZE tokens.

    Args:
        doc  : dict avec clés source, folder, content
        encoder : tiktoken encoder (réutilisé pour perf)

    Returns:
        list[dict] avec clés chunk_id, source, folder, text, token_count
    """
    if encoder is None:
        encoder = _get_encoder()

    source  = doc["source"]
    folder  = doc["folder"]
    content = _clean_text(doc["content"])

    tokens   = encoder.encode(content)
    n_tokens = len(tokens)

    if n_tokens == 0:
        return []

    chunks   = []
    chunk_idx = 0
    start     = 0

    while start < n_tokens:
        end = min(start + CHUNK_SIZE, n_tokens)

        # Essaie de couper sur une frontière naturelle (phrase/paragraphe)
        # en regardant les 30 derniers tokens
        if end < n_tokens:
            chunk_tokens = tokens[start:end]
            chunk_text_raw = encoder.decode(chunk_tokens)
            # Cherche le dernier point/saut de ligne dans les 60 derniers chars
            cut = max(
                chunk_text_raw.rfind(". "),
                chunk_text_raw.rfind(".\n"),
                chunk_text_raw.rfind("\n\n"),
            )
            if cut > len(chunk_text_raw) * 0.6:  # coupe seulement si proche de la fin
                chunk_text = chunk_text_raw[: cut + 1].strip()
                # Recalcule les tokens réels pour ce chunk
                chunk_tokens = encoder.encode(chunk_text)
            else:
                chunk_text = chunk_text_raw.strip()
        else:
            chunk_tokens = tokens[start:end]
            chunk_text = encoder.decode(chunk_tokens).strip()

        if chunk_text:
            # ID : base_fichier_chunk_000
            base = re.sub(r"[^a-z0-9]+", "_", source.lower().rsplit(".", 1)[0])
            chunk_id = f"{base}_chunk_{chunk_idx:03d}"

            chunks.append({
                "chunk_id":    chunk_id,
                "source":      source,
                "folder":      folder,
                "text":        chunk_text,
                "token_count": len(chunk_tokens),
            })
            chunk_idx += 1

        # Avance avec overlap
        step = len(encoder.encode(chunk_text)) - CHUNK_OVERLAP
        step = max(step, 50)  # évite boucle infinie
        start += step

    return chunks


def chunk_documents(documents: List[dict]) -> List[dict]:
    """
    Découpe une liste de documents en chunks.

    Returns:
        list de tous les chunks, tous documents confondus
    """
    encoder    = _get_encoder()
    all_chunks = []

    for doc in documents:
        doc_chunks = chunk_document(doc, encoder)
        all_chunks.extend(doc_chunks)
        log.info(f"  Chunké [{doc['type'].upper():4s}] {doc['source']}: {len(doc_chunks)} chunks")

    log.info(f"\nTotal chunks : {len(all_chunks)}")
    return all_chunks
