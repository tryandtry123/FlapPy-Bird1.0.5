import pygame
import sys
sys.path.append('.')  # 添加当前目录到路径

from src.utils import GameConfig, Window, Images, Sounds
from src.entities.boss import Boss, BossType

# 初始化pygame
pygame.init()
window = Window(288, 512)
screen = pygame.display.set_mode((window.width, window.height))
images = Images()

# 创建游戏配置
config = GameConfig(
    screen=screen,
    clock=pygame.time.Clock(),
    fps=30,
    window=window,
    images=images,
    sounds=Sounds(),
)

# 创建Boss实例
boss = Boss(config, BossType.NORMAL)

# 简单的测试循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # 清屏
    screen.fill((0, 0, 0))
    
    # 更新和绘制Boss
    boss.tick()
    
    # 更新显示
    pygame.display.flip()
    config.clock.tick(30)

pygame.quit() 