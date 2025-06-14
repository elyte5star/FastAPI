from modules.repository.queries.product import ProductQueries
from modules.queue.schema import Job, Task, Result
from asyncpg.exceptions import PostgresError
from collections.abc import Sequence


class JobTaskQueries(ProductQueries):
    async def add_job_to_db_query(self, job: Job) -> None:
        try:
            self.async_session.add(job)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def add_task_result_db_query(self, task_result: Result) -> None:
        try:
            self.async_session.add(task_result)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def add_task_to_db_query(self, task: Task) -> None:
        try:
            self.async_session.add(task)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()

    async def find_job_by_id(self, job_id: str) -> Job | None:
        return await self.async_session.get(Job, job_id)

    async def find_tasks_by_job_id(self, job_id: str) -> Sequence[Task]:
        stmt = self.select(Task).where(Task.job_id == job_id)
        result = await self.async_session.execute(stmt)
        tasks = result.scalars().all()
        return tasks

    async def find_result_by_task_id(self, task_id: str) -> Result | None:
        stmt = self.select(Result).where(Result.task_id == task_id)
        result = await self.async_session.execute(stmt)
        (task_result,) = result.first()
        return task_result

    async def get_jobs_query(self) -> Sequence[Job]:
        stmt = self.select(Job).order_by(Job.created_at)
        result = await self.async_session.execute(stmt)
        jobs = result.scalars().all()
        return jobs

    async def delete_job_by_id_query(self, job_id: str) -> None:
        try:
            stmt = self.delete(Job).where(Job.id == job_id)
            await self.async_session.execute(stmt)
        except PostgresError:
            await self.async_session.rollback()
            raise
        else:
            await self.async_session.commit()
