from abc import ABC, abstractmethod

from core.schemas import Storyboard, VideoTask


class BaseAgent(ABC):
    """
    所有业务 Agent 的基础类。

    每个 Agent 都必须接收 VideoTask，
    并返回 Storyboard。
    """

    name = "base_agent"

    @abstractmethod
    async def run(
        self,
        task: VideoTask,
    ) -> Storyboard:
        """
        执行 Agent 任务。

        参数：
            task：视频制作任务。

        返回：
            Storyboard：Agent 规划出的分镜。
        """
        raise NotImplementedError