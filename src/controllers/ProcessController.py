from .BaseController import BaseController
from .ProjectController import ProjectController
import os
import re
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from models import ProcessingEnum
from typing import List
from dataclasses import dataclass

@dataclass
class Document:
    page_content: str
    metadata: dict

class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self, file_id: str):
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(self.project_path, file_id)

        if not os.path.exists(file_path):
            return None

        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        return None

    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)
        if loader:
            return loader.load()
        return None

    def process_file_content(self, file_content: list, file_id: str,
                             chunk_size: int = 100, overlap_size: int = 20,
                             chunking_mode: str = "qa"):
        file_content_texts = [rec.page_content for rec in file_content]
        file_content_metadata = [rec.metadata for rec in file_content]

        if chunking_mode == "qa":
            chunks = self.process_qa_splitter(
                texts=file_content_texts,
                metadatas=file_content_metadata,
                chunk_size=chunk_size,
                overlap_size=overlap_size,
            )
        else:
            chunks = self.process_simpler_splitter(
                texts=file_content_texts,
                metadatas=file_content_metadata,
                chunk_size=chunk_size,
            )
        return chunks

    # ------------------------------------------------------------------
    # Arabic Q&A-aware chunker
    # ------------------------------------------------------------------
    def process_qa_splitter(self, texts: List[str], metadatas: List[dict],
                            chunk_size: int, overlap_size: int = 20):
        """
        Parses text structured as Arabic Q&A fatwa pairs:
            السؤال: <question text>
            الإجابة: <answer text>

        Strategy
        --------
        - Each Q+A pair is the primary semantic unit.
        - If the full pair fits within chunk_size characters → one chunk.
        - If the answer is too long → split on sentence/newline boundaries,
          prepending the question to *every* sub-chunk so that embedding
          models always see the question context.
        - Overlap carries the last `overlap_size` chars from the previous
          sub-chunk's answer segment into the next one.
        """
        SENTENCE_SPLIT = re.compile(r'(?<=[.؟!،\n])\s+')

        full_text = "\n".join(texts)

        # Split into individual Q+A blocks on every occurrence of السؤال:
        raw_blocks = re.split(r'(?=السؤال:)', full_text)

        chunks = []

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue

            # Separate question from answer
            match = re.match(r'(السؤال:.*?)(الإجابة:.*)', block, re.DOTALL)

            # Block has no answer marker — keep as a fallback simple chunk
            if not match:
                if len(block) > 1:
                    chunks.append(Document(
                        page_content=block,
                        metadata={"chunk_type": "simple"}
                    ))
                continue

            question = match.group(1).strip()
            answer   = match.group(2).strip()
            full_pair = question + "\n" + answer

            # ── Case 1: Pair fits in one chunk ──────────────────────────
            if len(full_pair) <= chunk_size:
                chunks.append(Document(
                    page_content=full_pair,
                    metadata={"chunk_type": "qa_full"}
                ))
                continue

            # ── Case 2: Answer too long — split it ──────────────────────
            sentences = SENTENCE_SPLIT.split(answer)
            sentences = [s for s in sentences if s.strip()]

            current_answer = ""
            part = 1

            for sentence in sentences:
                candidate = question + "\n" + current_answer + sentence

                if len(candidate) > chunk_size and current_answer:
                    # Emit current chunk
                    chunks.append(Document(
                        page_content=(question + "\n" + current_answer).strip(),
                        metadata={"chunk_type": "qa_part", "part": part}
                    ))
                    part += 1

                    # Overlap: carry the last `overlap_size` chars of the
                    # emitted answer segment into the next chunk
                    overlap_text = (
                        current_answer[-overlap_size:]
                        if len(current_answer) > overlap_size
                        else current_answer
                    )
                    current_answer = overlap_text + sentence + " "
                else:
                    current_answer += sentence + " "

            # Emit remaining answer text
            if current_answer.strip():
                chunks.append(Document(
                    page_content=(question + "\n" + current_answer).strip(),
                    metadata={"chunk_type": "qa_part", "part": part}
                ))

        return chunks

    # ------------------------------------------------------------------
    # Original simple splitter (kept for backward-compat with PDF / generic TXT)
    # ------------------------------------------------------------------
    def process_simpler_splitter(self, texts: List[str], metadatas: List[dict],
                                  chunk_size: int, splitter_tag: str = "\n"):
        full_text = " ".join(texts)

        lines = [doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip()) > 1]

        chunks = []
        current_chunk = ""

        for line in lines:
            current_chunk += line + splitter_tag

            if len(current_chunk) >= chunk_size:
                chunks.append(Document(
                    page_content=current_chunk.strip(),
                    metadata={}
                ))
                current_chunk = ""

        if current_chunk.strip():
            chunks.append(Document(
                page_content=current_chunk.strip(),
                metadata={}
            ))

        return chunks
