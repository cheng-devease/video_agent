"""图像处理工具 - 抠图、合成等"""
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("image_process")


class ImageProcessTool:
    """图像处理基础工具"""

    def __init__(self):
        self.temp_dir = Path(settings.temp_dir) / "processed"
        self.temp_dir.mkdir(parents=True, exist_ok=True)


class RemoveBGTool(ImageProcessTool):
    """背景移除工具"""

    def __init__(self):
        super().__init__()

    def remove_background(
        self,
        image_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """移除图片背景"""
        logger.info(f"Removing background: {image_path}")

        try:
            from rembg import remove

            with open(image_path, "rb") as f:
                input_data = f.read()

            output_data = remove(input_data)

            if not output_path:
                output_path = str(self.temp_dir / f"nobg_{Path(image_path).stem}.png")

            with open(output_path, "wb") as f:
                f.write(output_data)

            logger.info(f"Background removed: {output_path}")
            return output_path

        except ImportError:
            logger.warning("rembg not installed, using simple background removal")
            return self._simple_remove_bg(image_path, output_path)

    def _simple_remove_bg(self, image_path: str, output_path: Optional[str]) -> str:
        """简单的背景移除（备用方案）"""
        img = Image.open(image_path).convert("RGBA")

        # 简单的白色背景移除
        datas = img.getdata()
        new_data = []
        for item in datas:
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        img.putdata(new_data)

        if not output_path:
            output_path = str(self.temp_dir / f"nobg_{Path(image_path).stem}.png")

        img.save(output_path, "PNG")
        logger.info(f"Simple background removed: {output_path}")
        return output_path


class ImageComposeTool(ImageProcessTool):
    """图像合成工具"""

    def __init__(self):
        super().__init__()

    def compose(
        self,
        background_path: str,
        foreground_path: str,
        position: Tuple[int, int] = (0, 0),
        scale: float = 1.0,
        output_path: Optional[str] = None,
    ) -> str:
        """合成图片"""
        logger.info(f"Composing images")

        background = Image.open(background_path).convert("RGBA")
        foreground = Image.open(foreground_path).convert("RGBA")

        # 调整前景大小
        if scale != 1.0:
            new_size = (int(foreground.width * scale), int(foreground.height * scale))
            foreground = foreground.resize(new_size, Image.Resampling.LANCZOS)

        # 合成
        background.paste(foreground, position, foreground)

        if not output_path:
            output_path = str(self.temp_dir / f"composed_{Path(background_path).stem}.png")

        background.save(output_path, "PNG")
        logger.info(f"Composed image saved: {output_path}")
        return output_path

    def add_shadow(
        self,
        image_path: str,
        shadow_offset: Tuple[int, int] = (10, 10),
        shadow_blur: int = 10,
        output_path: Optional[str] = None,
    ) -> str:
        """添加阴影"""
        logger.info(f"Adding shadow to image")

        try:
            from PIL import ImageFilter

            img = Image.open(image_path).convert("RGBA")

            # 创建阴影层
            shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))

            # 提取alpha通道创建阴影形状
            alpha = img.split()[3]
            shadow_shape = Image.new("RGBA", img.size, (0, 0, 0, 128))
            shadow_shape.putalpha(alpha)

            # 模糊阴影
            shadow_shape = shadow_shape.filter(ImageFilter.GaussianBlur(shadow_blur))

            # 合成
            result = Image.new("RGBA", img.size, (0, 0, 0, 0))
            result.paste(shadow_shape, shadow_offset, shadow_shape)
            result.paste(img, (0, 0), img)

            if not output_path:
                output_path = str(self.temp_dir / f"shadow_{Path(image_path).stem}.png")

            result.save(output_path, "PNG")
            logger.info(f"Shadow added: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to add shadow: {e}")
            return image_path

    def resize_to_target(
        self,
        image_path: str,
        target_width: int,
        target_height: int,
        keep_aspect_ratio: bool = True,
        output_path: Optional[str] = None,
    ) -> str:
        """调整图片大小"""
        logger.info(f"Resizing image to {target_width}x{target_height}")

        img = Image.open(image_path)

        if keep_aspect_ratio:
            img.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        if not output_path:
            output_path = str(self.temp_dir / f"resized_{Path(image_path).stem}.png")

        img.save(output_path)
        logger.info(f"Resized image saved: {output_path}")
        return output_path
