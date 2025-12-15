from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId

class AssetModel(BaseDataModel): # responsible for the Project Collection
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance
    
    
    async def create_asset(self,asset:Asset):

        result = await self.collection.insert_one(asset.dict(by_alias=True,exclude_unset=True))
        asset.asset_id =  result.inserted_id
        return asset
    
    async def get_all_project_assets(self, asset_project_id: str, asset_type: str):
        records =  await self.collection.find({
            "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id,str) else asset_project_id,
            "asset_type": asset_type
            }).to_list(length=None) # length=None means return all documents
        
        return [
            Asset(**record)
            for record in records
        ]  # convert the record to a Asset Pydantic instance
    
    async def get_asset_record(self,asset_project_id: str, asset_name: str):
        record = await self.collection.find_one({
            "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id,str) else asset_project_id,
            "asset_name": asset_name
        })
        if record:
            return Asset(**record)
        return None 
