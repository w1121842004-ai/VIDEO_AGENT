import json
from pathlib import Path

from core.enums import JobStage, JobStatus
from core.schemas import GenerationJob, StoryboardScene, VideoTask
from tools.video.mock_status import MockJobStatusChecker


class MockVideoGenerator:
    """
    模拟视频生成模型。

    它不会真实生成 MP4，而是生成一个 JSON 文件，
    用来记录视频生成所需要的输入。
    """

    def __init__(
        self,
        output_dir: str | Path,
        status_checker: MockJobStatusChecker | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.status_checker = status_checker

    async def generate(
        self,
        task: VideoTask,
        scene: StoryboardScene,
        image_url: str,
    ) -> GenerationJob:
        """
        根据图片结果和分镜，生成一个模拟视频任务。
        """
        scene_dir = self.output_dir / task.task_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        output_path = scene_dir / f"scene-{scene.scene_id:03d}.json"

        payload = {
            "mock": True,
            "asset_type": "generated_video",
            "task_id": task.task_id,
            "scene_id": scene.scene_id,
            "source_image": image_url,
            "duration_seconds": scene.duration_seconds,
            "camera_motion": scene.camera_motion,
            "status": "generated",
        }

        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        job = GenerationJob(
            job_id=f"mock-video-{task.task_id}-{scene.scene_id}",
            task_id=task.task_id,
            stage=JobStage.VIDEO_GENERATION,
            provider="mock-video",
            status=JobStatus.SUCCEEDED,
            result_url=str(output_path),
        )

        if self.status_checker is not None:
            self.status_checker.register(job)

        return job