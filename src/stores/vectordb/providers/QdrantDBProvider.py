from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VectorDBInterface
import logging
from ..VectorDBEnums import DistanceMethodEnums
from typing import List

class QdrantDBProvider(VectorDBInterface):
    
    def __init__(self, db_path: str, distance_method: str):

        self.client = None
        self.db_path = db_path
        self.distnace_method = None

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distnace_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distnace_method = models.Distance.DOT

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.client = QdrantClient(path = self.db_path)
    
    def disconnect(self):
        self.client = None

    def is_collection_existed(self, collection_name) -> bool:
        return self.client.collection_exists(collection_name = collection_name)
    
    def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name) -> dict:
        return self.client.get_collection(collection_name = collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name=collection_name):
            return self.client.delete_collection(collection_name = collection_name)

    def create_collection(self, collection_name: str,
                          embedding_size: int,
                          do_reset: bool=False):        
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name) # _ means it will return a value but it's not important to me to use it again.
        
        if not self.is_collection_existed(collection_name=collection_name):
            _ = self.client.create_collection(collection_name,
                                              vectors_config=models.VectorParams(
                                                  size= embedding_size,
                                                  distance= self.distnace_method
                                                )
                                              )
            return True
        return False
    
    def insert_one(self, collection_name: str, text: str, vector: list,
                        metadata: dict = None,
                        record_id: str = None):
        if not self.is_collection_existed(collection_name=collection_name):
            self.logger.error(f"can not insert new record to non-existed collection: {collection_name}")
            return False
        try:
            _ = self.client.upload_records(collection_name=collection_name,
                                        records=[
                                            models.Record(
                                                vector=vector,
                                                payload={
                                                    "text": text,
                                                    "metadata": metadata
                                                }
                                            )
                                        ])
        except Exception as e:
            self.logger.error(f"error while inserting batch: {e}")
            return False
        
        return True

    def insert_many(self, collection_name: str, texts: list,
                     vectors: list, metadata: list = None,
                    record_ids: list = None, batch_size: int = 50):
            if metadata is None:
                metadata = [None] * len(texts)

            if record_ids is None:
                record_ids = [None] *  len(texts)
            for i in range(0, len(texts), batch_size):
                batch_end = i + batch_size

                batch_texts = texts[i:batch_end]
                batch_vectors = vectors[i:batch_end]
                batch_metadata = metadata[i:batch_end]

                batch_records = [
                    models.Record(
                            vector=batch_vectors[x],
                            payload={
                                        "text": batch_texts[x],
                                        "metadata": batch_metadata[x]
                                    }
                            )
                    for x in range(len(batch_texts))
                ]
                try:
                    _ = self.client.upload_records(
                        collection_name = collection_name,
                        records = batch_records
                    )
                except Exception as e:
                    self.logger.error(f"Error while inserting batch: {e}")
                    return False
            return True
    
    def search_by_vector(self, collection_name: str, vector: list, limit: int=5):
        
        return self.client.search(
            collection_name = collection_name,
            query_vector = vector,
            limit=limit
        )
