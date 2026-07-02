from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json
import logging


class NLPController(BaseController):

    def __init__(self, vectordb_client, generation_client, 
                 embedding_client, template_parser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.logger = logging.getLogger(__name__)

    def create_collection_name(self, project_id: str):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()
    
    async def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name=collection_name)
    
    async def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info =await self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads( # loads convert from string -> json
            json.dumps(collection_info, default=lambda x: x.__dict__)   # dumps convert object->string of json
        )
    
    async def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                                   chunks_ids: List[int], 
                                   do_reset: bool = False):
        
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: manage items
        texts = [ c.chunk_text for c in chunks ] # extract list of text("chunk")
        metadata = [ c.chunk_metadata for c in  chunks] # same as above but for metadata for each chunk
        vectors = self.embedding_client.embed_text(text=texts, 
                                             document_type=DocumentTypeEnum.DOCUMENT.value)

        # step3: create collection if not exists
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )

        # step4: insert into vector db
        _ = await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids,
        )

        return True

    async def search_vector_db_collection(self, project: Project, text: str, limit: int=10):
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: get text embedding vector
        query_vector =None
        vectors = self.embedding_client.embed_text(
            text = text,
            document_type = DocumentTypeEnum.QUERY.value
        )


        if not vectors or len(vectors) == 0:
            return False
        
        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0] # take first vector if multiple are returned
        
        if not query_vector:
            return False
        
        # step3: do sematic search
        results = await self.vectordb_client.search_by_vector(
            collection_name = collection_name,
            vector = query_vector,
            limit=limit
        )

        if not results:
            return False

        return results
    
    def rewrite_query(self, query: str, chat_history: list) -> str:
        """
        Uses the LLM to reformulate a follow-up question into a fully
        self-contained standalone question by incorporating the conversation
        history. Falls back to the original query if history is empty or
        the rewrite call fails.
        """
        if not chat_history:
            return query

        try:
            # Build a readable chat history string for the prompt
            history_lines = []
            for msg in chat_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    history_lines.append(f"المستخدم: {content}")
                elif role == "assistant":
                    history_lines.append(f"المساعد: {content}")

            history_str = "\n".join(history_lines)

            rewriter_system = self.template_parser.get("rag", "query_rewriter_system_prompt")
            rewriter_prompt = self.template_parser.get("rag", "query_rewriter_prompt", {
                "chat_history": history_str,
                "query": query,
            })

            rewrite_history = [
                self.generation_client.construct_prompt(
                    prompt=rewriter_system,
                    role=self.generation_client.enums.SYSTEM.value,
                )
            ]

            rewritten = self.generation_client.generate_text(
                prompt=rewriter_prompt,
                chat_history=rewrite_history,
            )

            if rewritten and rewritten.strip():
                return rewritten.strip()
        except Exception as e:
            self.logger.warning(f"Query rewriting failed, using original query. Error: {e}")

        return query

    async def answer_rag_question(self, project: Project, query: str,
                                  limit: int = 10, chat_history: list = []):

        answer, full_prompt, llm_chat_history = None, None, None

        # step1: rewrite query using conversation history
        standalone_query = self.rewrite_query(query=query, chat_history=chat_history)

        # step2: retrieve related documents using the rewritten standalone query
        retrieved_documents = await self.search_vector_db_collection(
            project=project,
            text=standalone_query,
            limit=limit,
        )

        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt, llm_chat_history

        # step3: Construct LLM prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")

        documents_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(doc.text),
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        # Use original query in the footer (not the rewritten one) for a natural response
        footer_prompt = self.template_parser.get("rag", "footer_prompt", {
            "query": query
        })

        # step4: Build generation history: system prompt + prior conversation turns
        llm_chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ] + chat_history

        full_prompt = "\n\n".join([documents_prompts, footer_prompt])

        # step5: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=llm_chat_history
        )

        return answer, full_prompt, llm_chat_history

    async def search_vector_db_all_collections(self, text: str, limit: int=10):
        # step1: get collection prefix
        prefix = f"collection_{self.vectordb_client.default_vector_size}_"

        # step2: get text embedding vector
        query_vector = None
        vectors = self.embedding_client.embed_text(
            text = text,
            document_type = DocumentTypeEnum.QUERY.value
        )

        if not vectors or len(vectors) == 0:
            return False
        
        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0] # take first vector if multiple are returned
        
        if not query_vector:
            return False
        
        # step3: do sematic search across all collections
        results = await self.vectordb_client.search_all_collections_by_vector(
            prefix = prefix,
            vector = query_vector,
            limit=limit
        )

        if not results:
            return False

        return results

    async def answer_rag_question_global(self, query: str, limit: int = 10,
                                         chat_history: list = []):

        answer, full_prompt, llm_chat_history = None, None, None

        # step1: rewrite query using conversation history
        standalone_query = self.rewrite_query(query=query, chat_history=chat_history)

        # step2: retrieve related documents using the rewritten standalone query
        retrieved_documents = await self.search_vector_db_all_collections(
            text=standalone_query,
            limit=limit,
        )

        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt, llm_chat_history

        # step3: Construct LLM prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")

        documents_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": self.generation_client.process_text(doc.text),
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        # Use original query in the footer for a natural response
        footer_prompt = self.template_parser.get("rag", "footer_prompt", {
            "query": query
        })

        # step4: Build generation history: system prompt + prior conversation turns
        llm_chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ] + chat_history

        full_prompt = "\n\n".join([documents_prompts, footer_prompt])

        # step5: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=llm_chat_history
        )

        return answer, full_prompt, llm_chat_history
