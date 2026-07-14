import json
from pathlib import Path

from core.enums import JobStage, JobStatus
from core.schemas import GenerationJob, StoryboardScene, VideoTask
from tools.video.mock_status import MockJobStatusChecker


class MockImageGenerator:
    """
    模拟图片生成模型。

    它不会真正生成图片，只会生成一个 JSON 文件，
    用来模拟真实图片模型返回结果的过程。
    """

    def __init__(
        self,
        output_dir: str | Path,
        status_checker: MockJobStatusChecker | None = None,
    ) -> None:
        # 统一把输出目录转换成 Path，方便后续拼接路径。
        self.output_dir = Path(output_dir)

        # 状态查询器用于保存和查询生成任务。
        self.status_checker = status_checker

    async def generate(
        self,
        task: VideoTask,
        scene: StoryboardScene,
    ) -> GenerationJob:
        """
        根据任务和分镜，生成一个模拟图片任务。

        返回值：
            GenerationJob：图片生成任务记录。
        """
        scene_dir = self.output_dir / task.task_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        output_path = scene_dir / f"scene-{scene.scene_id:03d}.json"

        # 这里用 JSON 模拟图片生成结果。
        payload = {
            "mock": True,
            "asset_type": "generated_image",
            "task_id": task.task_id,
            "scene_id": scene.scene_id,
            "visual_prompt": scene.visual_prompt,
            "status": "generated",
        }

        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        job = GenerationJob(
            job_id=f"mock-image-{task.task_id}-{scene.scene_id}",
            task_id=task.task_id,
            stage=JobStage.IMAGE_GENERATION,
            provider="mock-image",
            status=JobStatus.SUCCEEDED,
            result_url=str(output_path),
        )

        # 如果传入状态查询器，就把任务注册进去。
        if self.status_checker is not None:
            self.status_checker.register(job)

        return job