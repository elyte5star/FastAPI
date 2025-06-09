from modules.repository.queries.queue import JobTaskQueries
from modules.repository.request_models.job import GetJobRequest, GetJobsRequest, Job


class JobHandler(JobTaskQueries):

    async def _get_job(self, req: GetJobRequest):
        pass

    async def _get_jobs(self, req: GetJobsRequest):
        pass

    async def get_job_status(self, req):
        pass

    async def get_job_response(self, job: Job):
        pass
