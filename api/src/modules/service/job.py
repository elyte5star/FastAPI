from modules.repository.queries.queue import JobTaskQueries


from modules.repository.request_models.job import GetJobRequest, GetJobsRequest
from modules.repository.response_models.job import GetJobResponse, GetJobsResponse


class JobHandler(JobTaskQueries):

    async def _get_job(self, req: GetJobRequest) -> GetJobResponse:
        return GetJobResponse()
        pass

    async def _get_jobs(self, req: GetJobsRequest) -> GetJobsResponse:
        return GetJobsResponse()

    async def _get_job_response(self):
        pass

    async def get_task(self):
        pass

    async def _check_job_and_tasks(self, job: Job):
        pass

    async def _check_job_result(self, job: Job):
        pass
