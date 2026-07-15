import json
from pathlib import Path

from core.enums import JobStatus, TaskStatus
from core.errors import GenerationError, InvalidTaskError
from core.schemas import (
    GenerationJob,
    Storyboard,
    TaskResult,
    VideoTask,
)
from tools.video.mock_image_generator import MockImageGenerator
from tools.video.mock_status import MockJobStatusChecker
from tools.video.mock_video_generator import MockVideoGenerator
from agents.base_agent import BaseAgent

class VideoWorkflow:
    """
    视频制作最小工作流。

    当前阶段使用 Mock Tools：
    1. 生成模拟图片
    2. 生成模拟视频
    3. 查询任务状态
    4. 保存最终结果

    后续接入真实模型时，只需要替换图片和视频工具，
    不需要修改这里的流程逻辑。
    """

    def __init__(
        self,
        image_generator: MockImageGenerator,
        video_generator: MockVideoGenerator,
        status_checker: MockJobStatusChecker,
        result_dir: str | Path,
    ) -> None:
        """
        初始化工作流。

        参数：
            image_generator：图片生成工具。
            video_generator：视频生成工具。
            status_checker：任务状态查询工具。
            result_dir：最终结果保存目录。
        """
        self.image_generator = image_generator
        self.video_generator = video_generator
        self.status_checker = status_checker
        self.result_dir = Path(result_dir)

    async def run_with_agent(
    self,
    task: VideoTask,
    agent: BaseAgent,
    ) -> TaskResult:
        """
    通过 Agent 自动生成分镜，并执行完整视频流程。

    执行过程：

    1. 把 VideoTask 交给 Agent。
    2. Agent 生成 Storyboard。
    3. 把 Storyboard 交给底层 run()。
    4. 底层 run() 调用图片和视频工具。
    5. 返回最终 TaskResult。

    参数：
        task：用户提交的视频任务。
        agent：主编排 Agent。

    返回：
        TaskResult：最终视频任务结果。
        """
    # Agent 负责理解任务并生成分镜计划。
        storyboard = await agent.run(task)

    # Pipeline 负责执行分镜计划。
        return await self.run(
            task=task,
        storyboard=storyboard,
        )
    
    async def run(
        self,
        task: VideoTask,
        storyboard: Storyboard,
    ) -> TaskResult:
        """
        执行完整的视频制作流程。

        流程：

        VideoTask
        → Storyboard
        → 图片生成
        → 视频生成
        → 结果汇总
        """
        # 第一步：校验任务和分镜是否合法。
        self._validate_task_and_storyboard(
            task=task,
            storyboard=storyboard,
        )

        image_urls: list[str] = []
        video_urls: list[str] = []

        # 当前阶段按照分镜顺序逐个处理镜头。
        for scene in storyboard.scenes:
            # 第二步：生成当前镜头的图片。
            image_job = await self.image_generator.generate(
                task=task,
                scene=scene,
            )

            # 第三步：解析图片任务状态。
            checked_image_job = await self._resolve_job_status(
                image_job,
            )

            # 如果图片生成失败，这里会抛出 GenerationError。
            self._ensure_job_succeeded(checked_image_job)

            # 成功任务必须包含结果地址。
            image_url = self._require_result_url(
                checked_image_job,
            )

            image_urls.append(image_url)

            # 第四步：根据图片生成当前镜头的视频。
            video_job = await self.video_generator.generate(
                task=task,
                scene=scene,
                image_url=image_url,
            )

            # 第五步：解析视频任务状态。
            checked_video_job = await self._resolve_job_status(
                video_job,
            )

            # 如果视频生成失败，这里会抛出 GenerationError。
            self._ensure_job_succeeded(checked_video_job)

            # 成功任务必须包含结果地址。
            video_url = self._require_result_url(
                checked_video_job,
            )

            video_urls.append(video_url)

        # 第六步：汇总所有镜头结果。
        return self._build_result(
            task=task,
            image_urls=image_urls,
            video_urls=video_urls,
        )

    async def _resolve_job_status(
        self,
        job: GenerationJob,
    ) -> GenerationJob:
        """
        判断是否需要继续查询任务状态。

        关键逻辑：

        - 如果任务已经成功，直接返回。
        - 如果任务已经失败，直接返回。
        - 如果任务已经取消，直接返回。
        - 如果任务仍在排队或处理中，再调用状态查询工具。

        这样可以避免失败任务没有注册到状态查询器时，
        因为查询不到 job_id 而产生 KeyError。
        """
        final_statuses = {
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }

        # 任务已经处于最终状态，不需要再次查询。
        if job.status in final_statuses:
            return job

        # queued 或 processing 状态需要继续查询。
        return await self.status_checker.get_status(
            job.job_id,
        )

    @staticmethod
    def _validate_task_and_storyboard(
        task: VideoTask,
        storyboard: Storyboard,
    ) -> None:
        """
        校验任务和分镜是否匹配。
        """
        # 任务 ID 不一致，说明分镜不是当前任务的分镜。
        if task.task_id != storyboard.task_id:
            raise InvalidTaskError(
                "task_id does not match storyboard.task_id",
            )

        # 分镜不能为空。
        if not storyboard.scenes:
            raise InvalidTaskError(
                "storyboard must contain at least one scene",
            )

    @staticmethod
    def _ensure_job_succeeded(
        job: GenerationJob,
    ) -> None:
        """
        检查生成任务是否成功。

        只有 succeeded 状态可以继续往下执行。
        """
        if job.status != JobStatus.SUCCEEDED:
            error_message = (
                job.error_message
                or "generation job failed"
            )

            raise GenerationError(error_message)

    @staticmethod
    def _require_result_url(
        job: GenerationJob,
    ) -> str:
        """
        确保成功任务返回了结果地址。
        """
        if not job.result_url:
            raise GenerationError(
                f"job {job.job_id} succeeded "
                "without result_url",
            )

        return job.result_url

    def _build_result(
        self,
        task: VideoTask,
        image_urls: list[str],
        video_urls: list[str],
    ) -> TaskResult:
        """
        汇总所有镜头结果，并写入 results 目录。

        当前 Mock 阶段不会生成真实 MP4，
        而是生成 final-video.json 作为模拟最终视频结果。
        """
        # 最终视频结果目录。
        video_dir = (
            self.result_dir
            / "videos"
            / task.task_id
        )

        # 任务清单目录。
        manifest_dir = self.result_dir / "manifests"

        # 自动创建所需目录。
        video_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        manifest_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 模拟最终视频文件。
        final_video_path = (
            video_dir / "final-video.json"
        )

        # 任务结果清单文件。
        manifest_path = (
            manifest_dir / f"{task.task_id}.json"
        )

        # 生成结果清单。
        manifest_data = {
            "task_id": task.task_id,
            "status": TaskStatus.SUCCEEDED.value,
            "images": image_urls,
            "videos": video_urls,
            "scenes": [
                {
                    "scene_index": index + 1,
                    "video_url": video_url,
                }
                for index, video_url in enumerate(video_urls)
            ],
        }

        # 保存任务清单。
        manifest_path.write_text(
            json.dumps(
                manifest_data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # Mock 阶段把所有分镜视频地址汇总起来。
        final_video_data = {
            "mock": True,
            "task_id": task.task_id,
            "source_videos": video_urls,
            "manifest": str(manifest_path),
        }

        # 保存模拟最终视频结果。
        final_video_path.write_text(
            json.dumps(
                final_video_data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # 返回统一的最终结果对象。
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.SUCCEEDED,
            video_url=str(final_video_path),
            image_urls=image_urls,
            manifest_url=str(manifest_path),
        )
    