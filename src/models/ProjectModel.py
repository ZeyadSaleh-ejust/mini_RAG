from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select

class ProjectModel(BaseDataModel): # responsible for the Project Collection
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance
    

    # for creating a Document
    async def create_project(self,project:Project):
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.commit() # Executes the SQL INSERT statement
            await session.refresh(project)
            
        return project
    
    async def get_project_or_create_one(self,project_id: int):
        async with self.db_client() as session:
             async with session.begin():
                  query = select(Project).where(Project.project_id == project_id)
                  project = query.scalar_one_or_none()
                  if project is None:
                       project = self.create_project(project = Project(project_id=project_id))
                       return project
                  else:
                       return project

    
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