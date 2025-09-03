from pydantic import BaseModel, Field, validator
from bson.objectid import ObjectId
from typing import Optional

class DataChunk(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict 
    chunk_order: int = Field(..., gt=0)
    chunk_project_id: ObjectId # for making sure the chunk belongs to a project as a relation 


    class Config:
        arbitrary_types_allowed = True

    @classmethod  # classmethod ==> staticmethod which doesn't need self 
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("chunk_project_id", 1)
                ],
                "name": "chunk_project_id_index_1",
                "unique": False  # Ensures that each project_id is unique in the collection
            }
        ]


