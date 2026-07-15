from core.errors import InvalidTaskError
from core.schemas import (
    Storyboard,
    StoryboardScene,
    VideoTask,
)
from agents.base_agent import BaseAgent


class FashionStreetAgent(BaseAgent):
    """
    女装街拍带货 Agent。

    当前版本是规则版 Agent：
    - 不调用真实大模型
    - 根据商品信息生成固定结构的分镜
    - 用于验证 Agent 的输入和输出协议

    后续会把这里的规则替换成大模型调用。
    """

    name = "fashion_street_agent"

    async def run(
        self,
        task: VideoTask,
    ) -> Storyboard:
        """
        根据女装任务生成 6 个街拍带货镜头。
        """
        category = task.product_info.get(
            "category",
            "fashion",
        )

        # 当前 Agent 只处理女装任务。
        if category not in {"fashion", "女装"}:
            raise InvalidTaskError(
                f"unsupported category: {category}",
            )

        product_name = task.product_info.get(
            "name",
            "这款女装",
        )

        selling_points = task.product_info.get(
            "selling_points",
            "显瘦、百搭、舒适",
        )

        scenes = [
            self._build_hook_scene(
                product_name=product_name,
                selling_points=selling_points,
            ),
            self._build_full_body_scene(
                product_name=product_name,
            ),
            self._build_detail_scene(
                product_name=product_name,
                selling_points=selling_points,
            ),
            self._build_movement_scene(
                product_name=product_name,
            ),
            self._build_matching_scene(
                product_name=product_name,
                selling_points=selling_points,
            ),
            self._build_cta_scene(
                product_name=product_name,
            ),
        ]

        return Storyboard(
            task_id=task.task_id,
            scenes=scenes,
        )

    @staticmethod
    def _build_hook_scene(
        product_name: str,
        selling_points: str,
    ) -> StoryboardScene:
        """
        第一镜：开头抓住用户注意力。
        """
        return StoryboardScene(
            scene_id=1,
            duration_seconds=3,
            camera_motion="快速推进到中近景",
            visual_prompt=(
                f"9:16竖屏，真实城市街拍，年轻女性模特穿着"
                f"{product_name}，自然光，画面干净高级，"
                f"突出{selling_points}，开头快速吸引观众"
            ),
            voiceover=(
                f"这件{product_name}，上身真的太显瘦了"
            ),
            subtitle="这件衣服上身真的太显瘦了",
        )

    @staticmethod
    def _build_full_body_scene(
        product_name: str,
    ) -> StoryboardScene:
        """
        第二镜：展示整体版型和上身效果。
        """
        return StoryboardScene(
            scene_id=2,
            duration_seconds=4,
            camera_motion="从上到下缓慢扫过全身",
            visual_prompt=(
                f"9:16竖屏，模特穿着{product_name}在城市街道行走，"
                "全身构图，展示整体版型、腰线和长度，"
                "自然步行，真实服装实拍质感"
            ),
            voiceover="版型特别友好，身材比例一下就出来了",
            subtitle="优化身材比例，显高显瘦",
        )

    @staticmethod
    def _build_detail_scene(
        product_name: str,
        selling_points: str,
    ) -> StoryboardScene:
        """
        第三镜：展示面料、领口和服装细节。
        """
        return StoryboardScene(
            scene_id=3,
            duration_seconds=4,
            camera_motion="近景慢扫服装细节",
            visual_prompt=(
                f"9:16竖屏，{product_name}服装细节特写，"
                f"展示面料纹理、领口、袖口和走线，"
                f"画面重点突出{selling_points}，"
                "柔和自然光，高清电商实拍"
            ),
            voiceover="面料看起来很有质感，细节也做得很到位",
            subtitle="面料有质感，细节做工精致",
        )

    @staticmethod
    def _build_movement_scene(
        product_name: str,
    ) -> StoryboardScene:
        """
        第四镜：通过走动展示服装动态效果。
        """
        return StoryboardScene(
            scene_id=4,
            duration_seconds=4,
            camera_motion="环绕模特半圈并轻微跟拍",
            visual_prompt=(
                f"9:16竖屏，模特穿着{product_name}自然转身和行走，"
                "展示服装垂感、舒适度和动态效果，"
                "镜头轻微环绕，人物和服装保持一致"
            ),
            voiceover="走起来很轻松，日常通勤穿也完全不会累",
            subtitle="轻松舒适，日常通勤也能穿",
        )

    @staticmethod
    def _build_matching_scene(
        product_name: str,
        selling_points: str,
    ) -> StoryboardScene:
        """
        第五镜：展示服装搭配场景。
        """
        return StoryboardScene(
            scene_id=5,
            duration_seconds=4,
            camera_motion="中景横向移动",
            visual_prompt=(
                f"9:16竖屏，模特穿着{product_name}搭配简约鞋包，"
                "展示通勤、约会和日常休闲三种穿搭氛围，"
                f"整体风格自然高级，突出{selling_points}"
            ),
            voiceover="一件衣服可以搭出好多种风格，真的很百搭",
            subtitle="一衣多穿，通勤约会都合适",
        )

    @staticmethod
    def _build_cta_scene(
        product_name: str,
    ) -> StoryboardScene:
        """
        第六镜：总结卖点并引导购买。
        """
        return StoryboardScene(
            scene_id=6,
            duration_seconds=3,
            camera_motion="镜头缓慢拉远，模特回头看向镜头",
            visual_prompt=(
                f"9:16竖屏，模特穿着{product_name}站在街边，"
                "自然微笑并看向镜头，服装完整展示，"
                "画面干净，适合添加购买引导字幕"
            ),
            voiceover=f"喜欢这件{product_name}的姐妹，可以直接下单",
            subtitle="喜欢就直接下单",
        )