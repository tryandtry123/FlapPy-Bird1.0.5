from .game_config import GameConfig
from .images import Images
from .sounds import Sounds
from .utils import clamp, get_hit_mask, pixel_collision
from .window import Window

# 添加字体助手函数
def get_font(name='SimHei', size=12, fallback_name=None):
    """获取指定名称和大小的字体，如果失败则使用后备字体"""
    import pygame
    try:
        return pygame.font.SysFont(name, size)
    except:
        try:
            if fallback_name:
                return pygame.font.SysFont(fallback_name, size) 
            else:
                # 尝试常见中文字体
                for font_name in ['Microsoft YaHei', 'SimHei', 'NSimSun', 'SimSun', 'STHeiti']:
                    try:
                        return pygame.font.SysFont(font_name, size)
                    except:
                        pass
                # 都失败了就用系统默认
                return pygame.font.Font(None, size)
        except:
            return pygame.font.Font(None, size)
