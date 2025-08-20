from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel): # responsible for the Project Collection
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
    
    # for creating a Document
    async def create_project(self,project:Project):
        # insert_one is talking a dictionary 
        # NOTE: as the function is async and motor is async you need to use await
        result = await self.collection.insert_one(project.dict(by_alias=True,exclude_unset=True))
        project._id =  result.inserted_id
        return project
    
    async def get_project_or_create_one(self,project_id: str):
        # find_one is returning a dictionary
        record = await self.collection.find_one({
            "project_id": project_id
            })
        if record is None:
            # create new project
            project = Project(project_id=project_id)
            project = await self.create_project(project)

            return project
        return Project(**record)  # convert the record to a Project Pydantic instance
    
    async def get_all_projects(self,page: int = 1, page_size: int = 10):
            # count total number of documents
            total_documents = await self.collection.count_documents({})
            total_pages = total_documents//page_size
            if total_documents % page_size>0:
                total_pages += 1

            # Cursors are lazy - they don't fetch data until you iterate through them
            cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)
            projects = []
            async for document in cursor:
                 projects.append(
                      Project(**document)
                 )
            return projects, total_pages