from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (DistanceMethodEnums, PgVectorTableSchemaEnums,
                              PgVectorDistanceMethodEnums, PgVectorIndexTypeEnums)
from models.db_schemes import RetrievedDocument
from typing import List
import logging
from sqlalchemy.sql import text as sql_text
import json

class PGVectorProvider(VectorDBInterface):
    def __init__(self, db_client, default_vector_size: int = 786,
                distance_method: str=None):
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.distance_method = distance_method
        self.pgvector_table_prefix = PgVectorTableSchemaEnums._PREFIX.value
        self.logger = logging.getLogger("uvicorn")

    async def connect(self):
        async with self.db_client as session:
            async with session.begin():

                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                ))
            await session.commit()

    async def disconnect(self):
        pass

    async def is_collection_existed(self,collection_name: str) -> bool:
        record = None
        async with self.db_client as session:
            async with session.begin():

                list_tbl = sql_text('SELECT * FROM pg_tables WHERE tablename = :collection_name')
                results = await session.execute(list_tbl, {"collection_name": collection_name})
                record = results.scaler_one_or_none()

        return record 
    
    async def list_all_collections(self) -> List:
        records = []
        async with self.db_client as session:
            async with session.begin():

                list_tbl = sql_text('SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix')
                results = await session.execute(list_tbl, {"prefix": self.pgvector_table_prefix})
                records = results.scalars().all()

        return records
    
    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client as session:
            async with session.begin():

                table_info_stmt = sql_text('''
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                    FROM pg_tables
                    WHERE tablename = :collection_name
                ''')
                count_sql = sql_text('SELECT COUNT(*) FROM :collection_name')
                table_info = await session.execute(table_info_stmt, {"collection_name": collection_name})
                record_count = await session.execute(count_sql, {"collection_name": collection_name})

                table_data = table_info.fetchone()
                if not table_data:
                    return None
                
                return {
                    "table_data": dict(table_data),
                    "record_count": record_count,
                }
            
    async def delete_collection(self, collection_name: str):
        async with self.db_client as session:
            async with session.begin():

                delete_sql = sql_text('DROP TABLE IF EXISTS :collection_name')
                await session.execute(delete_sql, {"collection_name": collection_name})
                await session.commit()
            
        return True
