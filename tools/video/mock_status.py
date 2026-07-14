from core.schemas import GenerationJob


class MockJobStatusChecker:
    """
    模拟任务状态查询器。

    真实环境中，这里会请求即梦、Seedance 等平台的任务状态接口。
    当前阶段只把任务保存在内存中。
    """

    def __init__(self) -> None:
        # 使用字典保存 job_id 和对应的任务。
        self._jobs: dict[str, GenerationJob] = {}

    def register(self, job: GenerationJob) -> None:
        """
        注册一个生成任务。

        使用创建新字典的方式更新状态，
        避免直接修改原有字典对象。
        """
        self._jobs = {
            **self._jobs,
            job.job_id: job,
        }

    async def get_status(self, job_id: str) -> GenerationJob:
        """
        根据任务 ID 查询生成状态。

        当前使用 KeyError 表示任务不存在。
        后续可以替换成项目自己的 GenerationError。
        """
        return self._jobs[job_id]