"""产品信息数据模型"""
from dataclasses import dataclass, field
from typing import List, Optional
import json


@dataclass
class ProductInfo:
    """产品信息模型"""

    # 基础信息
    product_type: str = ""
    product_name: str = ""

    # 产品特征
    key_features: List[str] = field(default_factory=list)
    material: str = ""
    color_palette: List[str] = field(default_factory=list)
    shape_description: str = ""

    # 品牌信息
    brand_elements: List[str] = field(default_factory=list)
    brand_name: Optional[str] = None

    # 营销信息
    target_audience: str = ""
    selling_points: List[str] = field(default_factory=list)

    # 原始图片路径
    image_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "product_type": self.product_type,
            "product_name": self.product_name,
            "key_features": self.key_features,
            "material": self.material,
            "color_palette": self.color_palette,
            "shape_description": self.shape_description,
            "brand_elements": self.brand_elements,
            "brand_name": self.brand_name,
            "target_audience": self.target_audience,
            "selling_points": self.selling_points,
            "image_paths": self.image_paths,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "ProductInfo":
        return cls(
            product_type=data.get("product_type", ""),
            product_name=data.get("product_name", ""),
            key_features=data.get("key_features", []),
            material=data.get("material", ""),
            color_palette=data.get("color_palette", []),
            shape_description=data.get("shape_description", ""),
            brand_elements=data.get("brand_elements", []),
            brand_name=data.get("brand_name"),
            target_audience=data.get("target_audience", ""),
            selling_points=data.get("selling_points", []),
            image_paths=data.get("image_paths", []),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ProductInfo":
        return cls.from_dict(json.loads(json_str))

    def get_summary(self) -> str:
        parts = []
        if self.product_name:
            parts.append(f"产品名称: {self.product_name}")
        if self.product_type:
            parts.append(f"产品类型: {self.product_type}")
        if self.key_features:
            parts.append(f"关键特征: {', '.join(self.key_features[:3])}")
        return "\n".join(parts)
