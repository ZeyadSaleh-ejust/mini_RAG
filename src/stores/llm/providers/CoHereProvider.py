from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnum
import cohere
from cohere.errors.too_many_requests_error import TooManyRequestsError
import logging
import time
from typing import List, Union

class CoHereProvider(LLMInterface):

    def __init__(self, api_key: str,
                       default_input_max_characters: int=1000,
                       default_generation_max_output_tokens: int=1000,
                       default_generation_temperature: float=0.1):
        
        self.api_key = api_key

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.Client(api_key=self.api_key)

        self.enums = CoHereEnums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, chat_history: list=[], max_output_tokens: int=None,
                            temperature: float = None):

        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for CoHere was not set")
            return None
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        response = self.client.chat(
            model = self.generation_model_id,
            chat_history = chat_history,
            message = self.process_text(prompt),
            temperature = temperature,
            max_tokens = max_output_tokens
        )

        if not response or not response.text:
            self.logger.error("Error while generating text with CoHere")
            return None
        
        return response.text
    
    def embed_text(self, text: Union[str, List[str]], document_type: str = None,
                   batch_size: int = 50, max_retries: int = 5, retry_delay: float = 60.0):
        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if isinstance(text, str):
            text = [text]

        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere was not set")
            return None

        # Fix: compare .value to .value so query type is correctly detected
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value
        else:
            input_type = CoHereEnums.DOCUMENT.value

        all_embeddings = []

        for i in range(0, len(text), batch_size):
            batch = [self.process_text(t) for t in text[i:i + batch_size]]
            attempt = 0

            while attempt < max_retries:
                try:
                    response = self.client.embed(
                        model=self.embedding_model_id,
                        texts=batch,
                        input_type=input_type,
                        embedding_types=['float'],
                    )

                    if not response or not response.embeddings or not response.embeddings.float:
                        self.logger.error(f"Empty embedding response for batch {i // batch_size}")
                        return None

                    all_embeddings.extend(response.embeddings.float)
                    break  # success — move to next batch

                except TooManyRequestsError as e:
                    attempt += 1
                    wait = retry_delay * attempt  # linear back-off: 60s, 120s, 180s …
                    self.logger.warning(
                        f"Cohere 429 rate limit hit (batch {i // batch_size}, "
                        f"attempt {attempt}/{max_retries}). "
                        f"Waiting {wait:.0f}s before retry…"
                    )
                    if attempt >= max_retries:
                        self.logger.error("Max retries reached for Cohere embed. Aborting.")
                        raise
                    time.sleep(wait)

        return all_embeddings
        
    
    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "text": prompt
        }