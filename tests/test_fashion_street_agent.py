import pytest

from agents.fashion_street_agent import FashionStreetAgent
from agents.orchestrator_agent import OrchestratorAgent
from core.enums import AssetType
from core.errors import InvalidTaskError
from core.schemas import AssetRef, VideoTask


def build_fashion_task() -> VideoTask:
    """
    创建一个女装任务。

    这个测试数据模拟用户上传了一张女装商品图，
    同时提供商品名称和卖点。
    """
    product_image = AssetRef(
        asset_id="product-001",
        asset_type=AssetType.PRODUCT_IMAGE,
        uri="data/inputs/dress.png",
        mime_type="image/png",
    )

    return VideoTask(
        task_id="task-fashion-001",
        product_images=[product_image],
        product_info={
            "category": "fashion",
            "name": "轻薄显瘦通勤连衣裙",
            "selling_points": "轻薄、显瘦、通勤、百搭",
        },
    )


@pytest.mark.asyncio
async def test_fashion_agent_generates_storyboard() -> None:
    """
    测试女装 Agent 能生成完整分镜。
    """
    agent = FashionStreetAgent()

    storyboard = await agent.run(build_fashion_task())

    assert storyboard.task_id == "task-fashion-001"
    assert len(storyboard.scenes) == 6


@pytest.mark.asyncio
async def test_fashion_agent_includes_product_information() -> None:
    """
    测试生成的分镜包含商品名称和卖点。
    """
    agent = FashionStreetAgent()

    storyboard = await agent.run(build_fashion_task())

    all_prompts = " ".join(
        scene.visual_prompt
        for scene in storyboard.scenes
    )

    all_voiceovers = " ".join(
        scene.voiceover
        for scene in storyboard.scenes
    )

    assert "轻薄显瘦通勤连衣裙" in all_prompts
    assert "显瘦" in all_voiceovers


@pytest.mark.asyncio
async def test_orchestrator_routes_fashion_task() -> None:
    """
    测试主编排 Agent 能把女装任务路由给女装子 Agent。
    """
    fashion_agent = FashionStreetAgent()
    orchestrator = OrchestratorAgent(
        fashion_agent=fashion_agent,
    )

    storyboard = await orchestrator.run(
        build_fashion_task(),
    )

    assert storyboard.task_id == "task-fashion-001"
    assert len(storyboard.scenes) == 6


@pytest.mark.asyncio
async def test_orchestrator_rejects_unsupported_category() -> None:
    """
    测试当前不支持的品类会抛出明确异常。
    """
    task = build_fashion_task()

    unsupported_task = task.model_copy(
        update={
            "product_info": {
                "category": "automobile",
                "name": "汽车",
            },
        },
    )

    orchestrator = OrchestratorAgent(
        fashion_agent=FashionStreetAgent(),
    )

    with pytest.raises(InvalidTaskError):
        await orchestrator.run(unsupported_task)