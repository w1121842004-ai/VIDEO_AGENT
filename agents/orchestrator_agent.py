from agents.base_agent import BaseAgent
from agents.fashion_street_agent import FashionStreetAgent
from core.errors import InvalidTaskError
from core.schemas import Storyboard, VideoTask


class OrchestratorAgent(BaseAgent):
    """
    主编排 Agent。

    当前只支持女装品类。
    后续可以在这里注册更多子 Agent：
    - SportswearAgent
    - KidswearAgent
    - ShoesAgent
    """

    name = "orchestrator_agent"

    def __init__(
        self,
        fashion_agent: FashionStreetAgent,
    ) -> None:
        """
        注入女装子 Agent。

        使用依赖注入的好处是：
        测试时可以替换成 Mock Agent。
        """
        self.fashion_agent = fashion_agent

    async def run(
        self,
        task: VideoTask,
    ) -> Storyboard:
        """
        根据商品品类选择对应的子 Agent。
        """
        category = task.product_info.get(
            "category",
            "fashion",
        )

        if category in {"fashion", "女装"}:
            return await self.fashion_agent.run(task)

        raise InvalidTaskError(
            f"no agent registered for category: {category}",
        )