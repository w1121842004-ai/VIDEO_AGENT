import json

import pytest

from agents.fashion_street_agent import FashionStreetAgent
from agents.orchestrator_agent import OrchestratorAgent
from core.enums import AssetType, TaskStatus
from core.schemas import AssetRef, VideoTask
from pipeline.workflow import VideoWorkflow
from tools.video.mock_image_generator import MockImageGenerator
from tools.video.mock_status import MockJobStatusChecker
from tools.video.mock_video_generator import MockVideoGenerator


def build_fashion_task() -> VideoTask:
    """
    创建一个女装视频任务。

    这里模拟用户提供：
    1. 商品图片
    2. 商品品类
    3. 商品名称
    4. 商品卖点
    """
    product_image = AssetRef(
        asset_id="product-001",
        asset_type=AssetType.PRODUCT_IMAGE,
        uri="data/inputs/dress.png",
        mime_type="image/png",
    )

    return VideoTask(
        task_id="agent-task-001",
        product_images=[product_image],
        product_info={
            "category": "fashion",
            "name": "轻薄显瘦通勤连衣裙",
            "selling_points": "轻薄、显瘦、通勤、百搭",
        },
    )


@pytest.mark.asyncio
async def test_agent_can_drive_complete_workflow(tmp_path) -> None:
    """
    测试完整链路：

    VideoTask
    → OrchestratorAgent
    → FashionStreetAgent
    → Storyboard
    → Mock 图片生成
    → Mock 视频生成
    → TaskResult
    """
    status_checker = MockJobStatusChecker()

    image_generator = MockImageGenerator(
        output_dir=tmp_path / "images",
        status_checker=status_checker,
    )

    video_generator = MockVideoGenerator(
        output_dir=tmp_path / "videos",
        status_checker=status_checker,
    )

    workflow = VideoWorkflow(
        image_generator=image_generator,
        video_generator=video_generator,
        status_checker=status_checker,
        result_dir=tmp_path / "results",
    )

    fashion_agent = FashionStreetAgent()

    orchestrator = OrchestratorAgent(
        fashion_agent=fashion_agent,
    )

    result = await workflow.run_with_agent(
        task=build_fashion_task(),
        agent=orchestrator,
    )

    assert result.task_id == "agent-task-001"
    assert result.status == TaskStatus.SUCCEEDED
    assert len(result.image_urls) == 6
    assert result.video_url is not None
    assert result.manifest_url is not None

    manifest_path = tmp_path / "results" / "manifests" / "agent-task-001.json"

    assert manifest_path.exists()

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8"),
    )

    # 女装 Agent 当前默认生成 6 个镜头。
    assert len(manifest["scenes"]) == 6