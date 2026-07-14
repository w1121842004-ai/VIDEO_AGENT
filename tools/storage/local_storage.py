import shutil
from pathlib import Path

from core.errors import AssetNotFoundError


class LocalFileStorage:
    """
    本地文件存储工具。

    用于把输入素材或中间结果复制到指定目录。
    后续可以用同样的接口替换成 OSS、S3 等对象存储。
    """

    async def save(
        self,
        source_uri: str,
        target_path: str,
    ) -> str:
        """
        保存文件并返回目标文件路径。
        """
        source_path = Path(source_uri)
        destination_path = Path(target_path)

        # 输入文件不存在时，抛出明确的业务错误。
        if not source_path.is_file():
            raise AssetNotFoundError(
                f"source file not found: {source_uri}"
            )

        # 自动创建目标目录。
        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 保留文件元信息复制文件。
        shutil.copy2(source_path, destination_path)

        return str(destination_path)