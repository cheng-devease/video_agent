"""产品广告视频自动化工作流Agent - 入口文件"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from orchestrator.workflow import WorkflowOrchestrator
from agents.brand_composer import BrandAssets
from config.api_keys import api_keys
from config.settings import settings
from utils.logger import get_logger, setup_logger

logger = get_logger("main")


def validate_inputs(product_images: List[str]) -> bool:
    """验证输入图片"""
    if not product_images:
        logger.error("No product images provided")
        return False

    for img_path in product_images:
        if not Path(img_path).exists():
            logger.error(f"Image not found: {img_path}")
            return False

    return True


def check_api_keys() -> bool:
    """检查必需的API密钥"""
    missing = api_keys.validate_required_keys()
    if missing:
        logger.error(f"Missing required API keys: {', '.join(missing)}")
        logger.error("Please configure API keys in config/api_keys.py or set environment variables")
        return False

    # 检查视频生成API
    video_apis = api_keys.is_video_gen_configured()
    configured = [k for k, v in video_apis.items() if v]
    if not configured:
        logger.warning("No video generation APIs configured. Video generation will be disabled.")
    else:
        logger.info(f"Configured video APIs: {', '.join(configured)}")

    return True


async def generate_video(
    product_images: List[str],
    user_requirements: Optional[str] = None,
    logo_path: Optional[str] = None,
    cta_text: Optional[str] = None,
    background_music: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> str:
    """
    生成产品广告视频

    Args:
        product_images: 产品图片路径列表
        user_requirements: 用户需求描述
        logo_path: Logo图片路径
        cta_text: CTA文字
        background_music: 背景音乐路径
        output_dir: 输出目录

    Returns:
        str: 生成的视频路径
    """
    # 验证输入
    if not validate_inputs(product_images):
        raise ValueError("Invalid input images")

    # 检查API密钥
    if not check_api_keys():
        raise ValueError("Missing API keys")

    # 设置输出目录
    if output_dir:
        settings.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 准备品牌素材
    brand_assets = None
    if logo_path or cta_text or background_music:
        brand_assets = BrandAssets(
            logo_path=logo_path,
            cta_text=cta_text,
            background_music=background_music,
        )

    # 创建工作流编排器
    orchestrator = WorkflowOrchestrator()

    # 执行工作流
    logger.info("Starting video generation workflow...")
    logger.info(f"Product images: {len(product_images)}")
    logger.info(f"User requirements: {user_requirements or 'None'}")

    final_video = await orchestrator.run(
        product_images=product_images,
        user_requirements=user_requirements,
        brand_assets=brand_assets,
    )

    logger.info(f"Video generation completed: {final_video}")
    return final_video


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="产品广告视频自动化生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py -i product1.jpg product2.jpg -r "高端科技风格"
  python main.py -i product.jpg --logo brand.png --cta "立即购买"
  python main.py --list  # 列出所有工作流
        """,
    )

    parser.add_argument(
        "-i", "--images",
        nargs="+",
        help="产品图片路径 (1-5张)",
    )

    parser.add_argument(
        "-r", "--requirements",
        help="用户需求描述",
    )

    parser.add_argument(
        "--logo",
        help="Logo图片路径",
    )

    parser.add_argument(
        "--cta",
        help="CTA文字 (如: '立即购买')",
    )

    parser.add_argument(
        "--music",
        help="背景音乐路径",
    )

    parser.add_argument(
        "-o", "--output",
        help="输出目录",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有工作流",
    )

    parser.add_argument(
        "--status",
        help="查看工作流状态",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细日志输出",
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        setup_logger(log_level="DEBUG")

    # 列出工作流
    if args.list:
        orchestrator = WorkflowOrchestrator()
        workflows = orchestrator.list_workflows()
        if workflows:
            print("\n工作流列表:")
            for wf in workflows:
                print(f"  - {wf['workflow_id']}: {wf['status']} ({wf['progress']}%)")
        else:
            print("暂无工作流记录")
        return 0

    # 查看状态
    if args.status:
        orchestrator = WorkflowOrchestrator()
        state = orchestrator.get_state(args.status)
        if state:
            print(f"\n工作流状态: {state.workflow_id}")
            print(f"  状态: {state.status.value}")
            print(f"  进度: {state.progress}%")
            print(f"  当前步骤: {state.current_step}")
            print(f"  创建时间: {state.created_at}")
            if state.final_video_path:
                print(f"  输出视频: {state.final_video_path}")
            if state.error_message:
                print(f"  错误: {state.error_message}")
        else:
            print(f"工作流未找到: {args.status}")
        return 0

    # 生成视频
    if not args.images:
        parser.print_help()
        print("\n错误: 请提供产品图片 (-i, --images)")
        return 1

    try:
        final_video = asyncio.run(
            generate_video(
                product_images=args.images,
                user_requirements=args.requirements,
                logo_path=args.logo,
                cta_text=args.cta,
                background_music=args.music,
                output_dir=args.output,
            )
        )

        print(f"\n✅ 视频生成成功!")
        print(f"   输出文件: {final_video}")
        return 0

    except KeyboardInterrupt:
        print("\n用户取消")
        return 130

    except Exception as e:
        logger.error(f"视频生成失败: {e}")
        print(f"\n❌ 视频生成失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
