from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId  
# define each collection scheme here
class Project(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(..., min_length=1)

    # custom validation for any Field
    @validator('project_id')
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError('Project ID must be alphanumeric')
        return value
    
    class Config:
        arbitrary_types_allowed = True

    @classmethod  # classmethod ==> staticmethod which doesn't need self 
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("project_id", 1)
                ],
                "name": "project_id_index_1",
                "unique": True  # Ensures that each project_id is unique in the collection
            }
        ]