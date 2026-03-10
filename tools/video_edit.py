"""视频编辑工具 - MoviePy等"""
from pathlib import Path
from typing import Optional, List, Tuple
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("video_edit")


class VideoEditTool:
    """视频编辑基础工具"""

    def __init__(self):
        self.output_dir = Path(settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)


class MoviePyEditor(VideoEditTool):
    """MoviePy视频编辑器"""

    def __init__(self):
        super().__init__()
        from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, TextClip, AudioFileClip
        self.VideoFileClip = VideoFileClip
        self.CompositeVideoClip = CompositeVideoClip
        self.ImageClip = ImageClip
        self.TextClip = TextClip
        self.AudioFileClip = AudioFileClip

    def trim(self, video_path: str, start: float, end: float, output_path: Optional[str] = None) -> str:
        """裁剪视频"""
        logger.info(f"Trimming video: {start}s - {end}s")

        clip = self.VideoFileClip(video_path).subclip(start, end)

        if not output_path:
            output_path = str(self.output_dir / f"trimmed_{Path(video_path).stem}.mp4")

        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close()

        logger.info(f"Trimmed video saved: {output_path}")
        return output_path

    def add_logo(
        self,
        video_path: str,
        logo_path: str,
        position: Tuple[str, str] = ("right", "top"),
        logo_height: int = 50,
        output_path: Optional[str] = None,
    ) -> str:
        """添加Logo"""
        logger.info(f"Adding logo to video")

        video = self.VideoFileClip(video_path)
        logo = (self.ImageClip(logo_path)
                .set_duration(video.duration)
                .resize(height=logo_height)
                .set_position(position))

        final = self.CompositeVideoClip([video, logo])

        if not output_path:
            output_path = str(self.output_dir / f"branded_{Path(video_path).stem}.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()

        logger.info(f"Branded video saved: {output_path}")
        return output_path

    def add_text(
        self,
        video_path: str,
        text: str,
        position: Tuple[str, str] = ("center", "bottom"),
        fontsize: int = 30,
        color: str = "white",
        font: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """添加文字"""
        logger.info(f"Adding text to video")

        video = self.VideoFileClip(video_path)

        txt_clip = (self.TextClip(text, fontsize=fontsize, color=color, font=font)
                    .set_duration(video.duration)
                    .set_position(position))

        final = self.CompositeVideoClip([video, txt_clip])

        if not output_path:
            output_path = str(self.output_dir / f"text_{Path(video_path).stem}.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()

        logger.info(f"Text video saved: {output_path}")
        return output_path

    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        volume: float = 0.3,
        output_path: Optional[str] = None,
    ) -> str:
        """添加背景音乐"""
        logger.info(f"Adding audio to video")

        video = self.VideoFileClip(video_path)
        audio = self.AudioFileClip(audio_path).volumex(volume)

        # 循环或截取音频以匹配视频长度
        if audio.duration < video.duration:
            audio = audio.loop(duration=video.duration)
        else:
            audio = audio.subclip(0, video.duration)

        final = video.set_audio(audio)

        if not output_path:
            output_path = str(self.output_dir / f"audio_{Path(video_path).stem}.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()

        logger.info(f"Audio video saved: {output_path}")
        return output_path

    def concatenate(self, video_paths: List[str], output_path: Optional[str] = None) -> str:
        """拼接视频"""
        logger.info(f"Concatenating {len(video_paths)} videos")

        from moviepy.editor import concatenate_videoclips

        clips = [self.VideoFileClip(p) for p in video_paths]
        final = concatenate_videoclips(clips)

        if not output_path:
            output_path = str(self.output_dir / "concatenated.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")

        for clip in clips:
            clip.close()
        final.close()

        logger.info(f"Concatenated video saved: {output_path}")
        return output_path

    def resize(
        self,
        video_path: str,
        width: int,
        height: int,
        output_path: Optional[str] = None,
    ) -> str:
        """调整视频大小"""
        logger.info(f"Resizing video to {width}x{height}")

        clip = self.VideoFileClip(video_path)
        final = clip.resize((width, height))

        if not output_path:
            output_path = str(self.output_dir / f"resized_{Path(video_path).stem}.mp4")

        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()

        logger.info(f"Resized video saved: {output_path}")
        return output_path
