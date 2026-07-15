from pydantic import BaseModel, ConfigDict, Field

from core.enums import (
    AssetType,
    JobStage,
    JobStatus,
    TaskStatus,
)


class CoreModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class AssetRef(CoreModel):
    asset_id: str = Field(min_length=1)
    asset_type: AssetType
    uri: str = Field(min_length=1)
    mime_type: str | None = None


class VideoTask(CoreModel):
    task_id: str = Field(min_length=1)
    product_images: list[AssetRef] = Field(min_length=1)
    reference_video: AssetRef | None = None
    reference_audio: AssetRef | None = None
    video_ratio: str = "9:16"
    status: TaskStatus = TaskStatus.CREATED


class StoryboardScene(CoreModel):
    scene_id: int = Field(gt=0)
    duration_seconds: float = Field(gt=0)
    camera_motion: str = Field(min_length=1)
    visual_prompt: str = Field(min_length=1)
    voiceover: str = ""
    subtitle: str = ""


class Storyboard(CoreModel):
    task_id: str = Field(min_length=1)
    scenes: list[StoryboardScene] = Field(min_length=1)


class GenerationJob(CoreModel):
    job_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    stage: JobStage
    provider: str = Field(min_length=1)
    status: JobStatus = JobStatus.QUEUED
    result_url: str | None = None
    error_message: str | None = None


class TaskResult(CoreModel):
    task_id: str = Field(min_length=1)
    status: TaskStatus
    video_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    audio_url: str | None = None
    subtitle_url: str | None = None
    manifest_url: str | None = None

class VideoTask(CoreModel):
    """
    表示一个完整的视频制作任务。
    """

    task_id: str = Field(min_length=1)

    product_images: list[AssetRef] = Field(
        min_length=1,
    )

    # 保存商品名称、品类、卖点等业务信息。
    # 后续真实 Agent 会从商品图和用户描述中自动提取。
    product_info: dict[str, str] = Field(
        default_factory=dict,
    )

    reference_video: AssetRef | None = None
    reference_audio: AssetRef | None = None
    video_ratio: str = "9:16"
    status: TaskStatus = TaskStatus.CREATED