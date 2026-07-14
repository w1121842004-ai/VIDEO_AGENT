import json

import pytest

from core.enums import AssetType, JobStage, JobStatus
from core.errors import AssetNotFoundError
from core.schemas import AssetRef, StoryboardScene, VideoTask
from tools.storage.local_storage import LocalFileStorage
from tools.video.mock_image_generator import MockImageGenerator
from tools.video.mock_status import MockJobStatusChecker
from tools.video.mock_video_generator import MockVideoGenerator


def build_task() -> VideoTask:
    """创建一个测试用的视频任务。"""
    product_image = AssetRef(
        asset_id="product-001",
        asset_type=AssetType.PRODUCT_IMAGE,
        uri="data/inputs/dress.png",
        mime_type="image/png",
    )

    return VideoTask(
        task_id="task-001",
        product_images=[product_image],
    )


def build_scene() -> StoryboardScene:
    """创建一个测试用的分镜。"""
    return StoryboardScene(
        scene_id=1,
        duration_seconds=4,
        camera_motion="slow_push_in",
        visual_prompt="城市街拍，模特展示女装",
        voiceover="这件衣服真的很显瘦",
        subtitle="显瘦又百搭",
    )


@pytest.mark.asyncio
async def test_mock_image_generator_creates_result_file(tmp_path) -> None:
    """测试 Mock 图片工具能生成结果文件和任务记录。"""
    checker = MockJobStatusChecker()
    generator = MockImageGenerator(
        output_dir=tmp_path / "images",
        status_checker=checker,
    )

    job = await generator.generate(build_task(), build_scene())

    assert job.stage == JobStage.IMAGE_GENERATION
    assert job.status == JobStatus.SUCCEEDED
    assert job.result_url is not None

    result_file = tmp_path / "images" / "task-001" / "scene-001.json"
    assert result_file.exists()

    payload = json.loads(result_file.read_text(encoding="utf-8"))
    assert payload["scene_id"] == 1


@pytest.mark.asyncio
async def test_mock_video_generator_creates_result_file(tmp_path) -> None:
    """测试 Mock 视频工具能根据图片结果生成视频结果。"""
    checker = MockJobStatusChecker()
    generator = MockVideoGenerator(
        output_dir=tmp_path / "videos",
        status_checker=checker,
    )

    job = await generator.generate(
        task=build_task(),
        scene=build_scene(),
        image_url="mock://images/task-001/scene-001.json",
    )

    assert job.stage == JobStage.VIDEO_GENERATION
    assert job.status == JobStatus.SUCCEEDED
    assert job.result_url is not None

    result_file = tmp_path / "videos" / "task-001" / "scene-001.json"
    assert result_file.exists()


@pytest.mark.asyncio
async def test_job_status_checker_returns_registered_job(tmp_path) -> None:
    """测试状态查询工具能查询已经注册的任务。"""
    checker = MockJobStatusChecker()
    generator = MockImageGenerator(
        output_dir=tmp_path / "images",
        status_checker=checker,
    )

    created_job = await generator.generate(build_task(), build_scene())
    queried_job = await checker.get_status(created_job.job_id)

    assert queried_job.job_id == created_job.job_id
    assert queried_job.status == JobStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_job_status_checker_raises_for_unknown_job() -> None:
    """测试查询不存在的任务时能抛出明确错误。"""
    checker = MockJobStatusChecker()

    with pytest.raises(KeyError):
        await checker.get_status("unknown-job")


@pytest.mark.asyncio
async def test_local_storage_copies_file(tmp_path) -> None:
    """测试本地存储工具能复制素材文件。"""
    source_file = tmp_path / "source.txt"
    target_file = tmp_path / "nested" / "target.txt"

    source_file.write_text("video agent", encoding="utf-8")

    storage = LocalFileStorage()
    saved_path = await storage.save(
        source_uri=str(source_file),
        target_path=str(target_file),
    )

    assert saved_path == str(target_file)
    assert target_file.read_text(encoding="utf-8") == "video agent"


@pytest.mark.asyncio
async def test_local_storage_raises_for_missing_file(tmp_path) -> None:
    """测试保存不存在的文件时能抛出素材不存在错误。"""
    storage = LocalFileStorage()

    with pytest.raises(AssetNotFoundError):
        await storage.save(
            source_uri=str(tmp_path / "missing.txt"),
            target_path=str(tmp_path / "target.txt"),
        )