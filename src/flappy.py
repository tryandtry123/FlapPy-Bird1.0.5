import asyncio
import sys
import math

import pygame
from pygame.locals import K_ESCAPE, K_SPACE, K_UP, KEYDOWN, QUIT, K_q, K_e, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8

from .entities import (
    Background,
    Floor,
    GameOver,
    Pipes,
    Player,
    PlayerMode,
    Score,
    WelcomeMessage,
)
from .entities.powerup import PowerUpManager, PowerUpType, PowerUp
from .entities.boss import Boss, BossType
from .entities.bullet import Bullet
from .entities.weapon import WeaponType
from .entities.coin import CoinManager
from .utils import GameConfig, Images, Sounds, Window, get_font
from enum import Enum


class GameMode(Enum):
    """游戏模式枚举"""
    CLASSIC = "经典模式"    # 经典无限模式
    TIMED = "限时挑战"      # 限时挑战模式
    REVERSE = "重力反转"    # 重力反转模式
    BOSS = "Boss战斗"     # BOSS战模式
    COIN = "金币收集"     # 金币收集模式


class Flappy:
    def __init__(self):
        """
        初始化Flappy Bird游戏
        """
        pygame.init()  # 初始化pygame
        pygame.display.set_caption("Flappy Bird")  # 设置窗口标题
        window = Window(350, 600)  # 扩大窗口尺寸
        screen = pygame.display.set_mode((window.width, window.height))  # 设置屏幕大小
        images = Images()  # 加载图像资源

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=30,
            window=window,
            images=images,
            sounds=Sounds(),
        )
        # 设置调试模式为False，关闭调试信息显示
        self.config.debug = False
        # 记录上一帧的时间，用于计算delta_time
        self.last_frame_time = pygame.time.get_ticks()
        
        # 游戏模式相关
        self.game_mode = GameMode.CLASSIC  # 默认为经典模式
        self.time_limit = 60 * 1000  # 限时模式的时间限制（毫秒）
        self.time_remaining = self.time_limit  # 剩余时间
        
        # Boss相关
        self.boss = None
        self.boss_level = 0
        self.boss_cycle = 0  # 初始化Boss循环次数
        
        # 初始化道具管理器
        self.powerup_manager = PowerUpManager(self.config)
        
        # 初始化金币管理器
        self.coin_manager = CoinManager(self.config)
        
        # 初始化金币收集计数
        self.collected_coins = 0

    async def start(self):
        """
        启动游戏循环
        """
        while True:
            self.background = Background(self.config)  # 创建背景对象
            self.floor = Floor(self.config)  # 创建地面对象
            self.player = Player(self.config)  # 创建玩家对象
            self.welcome_message = WelcomeMessage(self.config)  # 创建欢迎信息对象
            self.game_over_message = GameOver(self.config)  # 创建游戏结束信息对象
            self.pipes = Pipes(self.config)  # 创建管道对象
            self.score = Score(self.config)  # 创建得分对象
            await self.splash()  # 显示欢迎界面
            await self.play()  # 开始游戏
            await self.game_over()  # 游戏结束

    async def splash(self):
        """
        显示欢迎界面和模式选择
        """
        self.player.set_mode(PlayerMode.SHM)  # 设置玩家模式为SHM（静止模式）
        
        # 初始化字体 - 使用中文字体
        title_font = get_font('SimHei', 36)  # 标题字体
        mode_font = get_font('SimHei', 24)   # 模式选择字体
        desc_font = get_font('SimHei', 14)   # 描述文字字体
        instruction_font = get_font('SimHei', 18)  # 指示字体
        
        # 创建文本
        title_text = title_font.render("FlappyBird", True, (255, 255, 255))  # 白色标题
        classic_text = mode_font.render("经典模式", True, (255, 255, 255))
        timed_text = mode_font.render("限时挑战", True, (255, 255, 255))
        reverse_text = mode_font.render("重力反转", True, (255, 255, 255))
        boss_text = mode_font.render("Boss战斗", True, (255, 255, 255))
        coin_text = mode_font.render("金币收集", True, (255, 255, 255))
        
        # 添加模式描述文本
        classic_desc = desc_font.render("无尽挑战的经典玩法", True, (220, 220, 220))
        timed_desc = desc_font.render("60秒内获得最高分", True, (220, 220, 220))
        reverse_desc = desc_font.render("颠倒重力，挑战不同体验", True, (220, 220, 220))
        boss_desc = desc_font.render("击败强大的Boss敌人", True, (220, 220, 220))
        coin_desc = desc_font.render("收集金币获取更高分数", True, (220, 220, 220))
        
        instruction_text = instruction_font.render("↑↓ 选择    空格 开始", True, (255, 255, 255))
        
        # 菜单颜色方案
        primary_color = (255, 204, 0)  # 主要颜色（金黄色）
        secondary_color = (87, 189, 255)  # 次要颜色（天蓝色）
        dark_color = (40, 40, 40, 220)  # 深色（带透明度）
        highlight_color = (255, 255, 255, 180)  # 高亮色（带透明度）
        
        # 计算文本位置
        window_center_x = self.config.window.width // 2
        title_pos = (window_center_x - title_text.get_width()//2, 60)
        
        # 计算菜单项位置和大小
        button_width = 200
        button_height = 50
        button_spacing = 65  # 按钮之间的间距
        button_start_y = 150
        
        # 创建一个半透明的菜单背景面板
        menu_panel_width = button_width + 60
        menu_panel_height = 395  # 增加高度以容纳新的金币模式按钮
        menu_panel = pygame.Surface((menu_panel_width, menu_panel_height), pygame.SRCALPHA)
        menu_panel.fill((0, 0, 0, 150))  # 半透明黑色
        menu_panel_pos = (window_center_x - menu_panel_width//2, button_start_y - 20)
        
        # 预设按钮位置
        button_x = window_center_x - button_width//2
        
        # 按钮位置列表
        button_positions = [
            button_start_y,
            button_start_y + button_spacing,
            button_start_y + button_spacing * 2,
            button_start_y + button_spacing * 3,
            button_start_y + button_spacing * 4  # 新增金币模式按钮位置
        ]
        
        # 为按钮创建矩形和描述文本位置
        button_rects = [
            pygame.Rect(button_x, button_positions[0], button_width, button_height),
            pygame.Rect(button_x, button_positions[1], button_width, button_height),
            pygame.Rect(button_x, button_positions[2], button_width, button_height),
            pygame.Rect(button_x, button_positions[3], button_width, button_height),
            pygame.Rect(button_x, button_positions[4], button_width, button_height)  # 新增金币模式按钮矩形
        ]
        
        # 描述文本位置
        desc_positions = [
            (window_center_x, button_positions[0] + button_height + 10),
            (window_center_x, button_positions[1] + button_height + 10),
            (window_center_x, button_positions[2] + button_height + 10),
            (window_center_x, button_positions[3] + button_height + 10),
            (window_center_x, button_positions[4] + button_height + 10)  # 新增金币模式描述位置
        ]
        
        # 创建按钮图标 - 使用简单的图形
        icons = []
        
        # 经典模式图标 - 管道
        classic_icon = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(classic_icon, (100, 200, 100), (8, 0, 8, 24))
        pygame.draw.rect(classic_icon, (80, 180, 80), (8, 0, 8, 6))
        icons.append(classic_icon)
        
        # 限时模式图标 - 时钟
        timed_icon = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(timed_icon, (200, 200, 200), (12, 12), 10, 2)
        pygame.draw.line(timed_icon, (200, 200, 200), (12, 12), (12, 6), 2)
        pygame.draw.line(timed_icon, (200, 200, 200), (12, 12), (16, 12), 2)
        icons.append(timed_icon)
        
        # 重力反转图标 - 上下箭头
        reverse_icon = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.polygon(reverse_icon, (150, 150, 250), [(12, 0), (18, 8), (14, 8), (14, 16), (18, 16), (12, 24), (6, 16), (10, 16), (10, 8), (6, 8)])
        icons.append(reverse_icon)
        
        # Boss模式图标 - 敌人
        boss_icon = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(boss_icon, (250, 100, 100), (12, 12), 10)
        pygame.draw.circle(boss_icon, (255, 255, 255), (8, 8), 3)
        pygame.draw.circle(boss_icon, (255, 255, 255), (16, 8), 3)
        pygame.draw.circle(boss_icon, (0, 0, 0), (8, 8), 1)
        pygame.draw.circle(boss_icon, (0, 0, 0), (16, 8), 1)
        pygame.draw.rect(boss_icon, (200, 50, 50), (8, 15, 8, 3))
        icons.append(boss_icon)
        
        # 金币模式图标 - 金币
        coin_icon = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(coin_icon, (255, 215, 0), (12, 12), 10)  # 金色圆形
        pygame.draw.circle(coin_icon, (255, 235, 100), (12, 12), 7)  # 浅金色内圈
        # 添加 "$" 符号
        try:
            coin_font = pygame.font.SysFont("Arial", 12, bold=True)
        except:
            coin_font = pygame.font.Font(None, 12)
        coin_text = coin_font.render("$", True, (100, 80, 0))
        coin_text_rect = coin_text.get_rect(center=(12, 12))
        coin_icon.blit(coin_text, coin_text_rect)
        icons.append(coin_icon)
        
        # 按钮文本
        button_texts = [classic_text, timed_text, reverse_text, boss_text, coin_text]
        desc_texts = [classic_desc, timed_desc, reverse_desc, boss_desc, coin_desc]
        
        # 初始动画数据
        button_animations = [0, 0, 0, 0, 0]  # 按钮动画计数器
        button_scale = [1.0, 1.0, 1.0, 1.0, 1.0]  # 按钮缩放因子
        
        # 默认选择经典模式
        self.game_mode = GameMode.CLASSIC
        selected_index = 0  # 0=经典, 1=限时, 2=反转, 3=Boss, 4=金币
        
        # 为游戏标题添加脉动效果
        title_scale = 1.0
        title_scale_dir = 0.0005
        
        # 计算指令文本位置
        instruction_pos = (window_center_x - instruction_text.get_width()//2, 
                          menu_panel_pos[1] + menu_panel_height + 20)

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)  # 检查退出事件
                
                # 处理模式选择
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        # 向下切换模式
                        selected_index = (selected_index + 1) % 5
                        if selected_index == 0:
                            self.game_mode = GameMode.CLASSIC
                        elif selected_index == 1:
                            self.game_mode = GameMode.TIMED
                            self.time_remaining = self.time_limit
                        elif selected_index == 2:
                            self.game_mode = GameMode.REVERSE
                        elif selected_index == 3:
                            self.game_mode = GameMode.BOSS
                        elif selected_index == 4:
                            self.game_mode = GameMode.COIN
                        self.config.sounds.swoosh.play()
                    elif event.key == pygame.K_UP:
                        # 向上切换模式
                        selected_index = (selected_index - 1) % 5
                        if selected_index == 0:
                            self.game_mode = GameMode.CLASSIC
                        elif selected_index == 1:
                            self.game_mode = GameMode.TIMED
                            self.time_remaining = self.time_limit
                        elif selected_index == 2:
                            self.game_mode = GameMode.REVERSE
                        elif selected_index == 3:
                            self.game_mode = GameMode.BOSS
                        elif selected_index == 4:
                            self.game_mode = GameMode.COIN
                        self.config.sounds.swoosh.play()
                
                # 空格或上箭头开始游戏
                if self.is_tap_event(event):
                    return
            
            # 更新标题动画
            title_scale += title_scale_dir
            if title_scale > 1.05:
                title_scale = 1.05
                title_scale_dir = -title_scale_dir
            elif title_scale < 0.95:
                title_scale = 0.95
                title_scale_dir = -title_scale_dir
            
            # 更新按钮动画
            for i in range(5):
                if i == selected_index:
                    # 选中的按钮放大动画
                    button_animations[i] += 0.1
                    if button_animations[i] > 1:
                        button_animations[i] = 1
                    button_scale[i] = 1.0 + 0.03 * math.sin(pygame.time.get_ticks() / 150)
                else:
                    # 未选中的按钮恢复正常
                    button_animations[i] -= 0.1
                    if button_animations[i] < 0:
                        button_animations[i] = 0
                    button_scale[i] = 1.0
            
            # 绘制背景、地面和玩家
            self.background.tick()
            self.floor.tick()
            self.player.tick()
            self.welcome_message.tick()
            
            # 绘制半透明菜单背景
            self.config.screen.blit(menu_panel, menu_panel_pos)
            
            # 绘制游戏标题
            scaled_title = pygame.transform.scale(
                title_text, 
                (int(title_text.get_width() * title_scale), 
                 int(title_text.get_height() * title_scale))
            )
            title_rect = scaled_title.get_rect(center=(window_center_x, title_pos[1] + title_text.get_height()//2))
            self.config.screen.blit(scaled_title, title_rect)
            
            # 绘制每个按钮
            for i in range(5):
                # 计算动画效果
                animation = button_animations[i]
                current_scale = button_scale[i]
                
                # 计算绘制矩形（添加缩放效果）
                scaled_width = int(button_width * current_scale)
                scaled_height = int(button_height * current_scale)
                button_x = window_center_x - scaled_width//2
                button_y = button_positions[i] - (scaled_height - button_height)//2
                
                draw_rect = pygame.Rect(button_x, button_y, scaled_width, scaled_height)
                
                # 绘制按钮背景和边框
                if i == selected_index:
                    # 选中的按钮 - 亮色渐变背景
                    bg_color = (
                        int(dark_color[0] + (primary_color[0] - dark_color[0]) * animation),
                        int(dark_color[1] + (primary_color[1] - dark_color[1]) * animation),
                        int(dark_color[2] + (primary_color[2] - dark_color[2]) * animation),
                        200
                    )
                    # 绘制背景
                    pygame.draw.rect(self.config.screen, bg_color, draw_rect, border_radius=10)
                    # 添加高亮边框
                    pygame.draw.rect(self.config.screen, primary_color, draw_rect, 3, border_radius=10)
                    # 添加发光效果
                    glow_surface = pygame.Surface((scaled_width+10, scaled_height+10), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surface, (primary_color[0], primary_color[1], primary_color[2], 50), 
                                   pygame.Rect(5, 5, scaled_width, scaled_height), border_radius=10)
                    self.config.screen.blit(glow_surface, (button_x-5, button_y-5))
                else:
                    # 未选中的按钮 - 暗色背景
                    pygame.draw.rect(self.config.screen, dark_color, draw_rect, border_radius=10)
                    pygame.draw.rect(self.config.screen, (100, 100, 100, 180), draw_rect, 2, border_radius=10)
                
                # 绘制按钮图标
                icon_size = int(24 * current_scale)
                scaled_icon = pygame.transform.scale(icons[i], (icon_size, icon_size))
                icon_x = button_x + 20
                icon_y = button_y + (scaled_height - icon_size) // 2
                self.config.screen.blit(scaled_icon, (icon_x, icon_y))
                
                # 绘制按钮文本
                text_x = button_x + icon_size + 30
                text_y = button_y + (scaled_height - button_texts[i].get_height()) // 2
                self.config.screen.blit(button_texts[i], (text_x, text_y))
                
                # 绘制按钮描述（只为选中的按钮显示）
                if i == selected_index:
                    desc_rect = desc_texts[i].get_rect(center=desc_positions[i])
                    self.config.screen.blit(desc_texts[i], desc_rect)
            
            # 绘制指令文本
            self.config.screen.blit(instruction_text, instruction_pos)
            
            pygame.display.update()  # 刷新显示
            await asyncio.sleep(0)  # 等待下一帧
            self.config.tick()  # 更新游戏配置

    def check_quit_event(self, event):
        """
        检查退出事件
        """
        if event.type == QUIT or (
            event.type == KEYDOWN and event.key == K_ESCAPE
        ):
            pygame.quit()  # 退出pygame
            sys.exit()  # 退出程序

    def is_tap_event(self, event):
        """
        检查点击事件
        """
        m_left, _, _ = pygame.mouse.get_pressed()  # 检查鼠标左键是否按下
        space_or_up = event.type == KEYDOWN and (
            event.key == K_SPACE or event.key == K_UP
        )  # 检查空格键或上箭头是否按下
        screen_tap = event.type == pygame.FINGERDOWN  # 检查触摸事件
        return m_left or space_or_up or screen_tap  # 返回是否有点击事件

    def calculate_delta_time(self):
        """
        计算两帧之间的时间差
        """
        current_time = pygame.time.get_ticks()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        return delta_time

    def check_powerup_collisions(self):
        """
        检查玩家与道具的碰撞
        """
        # 创建一个要删除的道具列表
        powerups_to_remove = []
        
        # 检查所有道具
        for powerup in self.powerup_manager.powerups:
            # 如果玩家碰到了道具
            if self.player.collide(powerup):
                # 激活道具在管理器中的效果
                self.powerup_manager.activate_effect(powerup.power_type)
                # 播放得分声音
                self.config.sounds.point.play()
                # 添加到要删除的列表
                powerups_to_remove.append(powerup)
        
        # 从管理器中删除已收集的道具
        for powerup in powerups_to_remove:
            if powerup in self.powerup_manager.powerups:
                self.powerup_manager.powerups.remove(powerup)

    def update_player_effects(self):
        """更新玩家的状态效果"""
        # 保存之前的速度修改器
        current_speed_modifier = 1.0
        current_invincible = False
        current_size_modifier = 1.0
        
        # 检查当前激活的效果
        for power_type in PowerUpType:
            if self.powerup_manager.has_effect(power_type):
                # 应用效果
                if power_type == PowerUpType.SPEED_BOOST:
                    current_speed_modifier = 1.5
                elif power_type == PowerUpType.INVINCIBLE:
                    current_invincible = True
                elif power_type == PowerUpType.SLOW_MOTION:
                    current_speed_modifier = 0.5
                elif power_type == PowerUpType.SMALL_SIZE:
                    current_size_modifier = 0.6
        
        # 应用最终效果
        self.player.speed_modifier = current_speed_modifier
        self.player.invincible = current_invincible
        self.player.size_modifier = current_size_modifier

    def render_active_effects(self):
        """
        在屏幕上显示当前激活的效果及其剩余时间
        """
        active_effects = []
        for power_type in PowerUpType:
            if self.powerup_manager.has_effect(power_type):
                remaining_ms = self.powerup_manager.get_remaining_time(power_type)
                if remaining_ms is not None:
                    active_effects.append((power_type, remaining_ms))
        
        # 如果有激活的效果，在屏幕上显示
        if active_effects:
            # 创建一个半透明背景面板 - 更精简的尺寸
            panel_width = 130
            panel_height = len(active_effects) * 20 + 8
            panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            panel_surface.fill((0, 0, 0, 180))  # 黑色半透明背景
            
            # 添加面板边框
            pygame.draw.rect(panel_surface, (255, 255, 255, 70), pygame.Rect(0, 0, panel_width, panel_height), 1)
            
            # 在屏幕左侧中部绘制面板
            panel_pos = (5, 40)  # 位置调整到左侧中部
            self.config.screen.blit(panel_surface, panel_pos)
            
            # 使用中文字体 - 更小的字体
            effect_font = get_font('SimHei', 12)
            
            # 处理每个激活的效果 - 不显示标题，直接显示效果
            for idx, (power_type, remaining_ms) in enumerate(active_effects):
                remaining_sec = remaining_ms / 1000
                y_pos = panel_pos[1] + 4 + idx * 20
                
                # 根据道具类型选择显示文本、颜色和图标
                if power_type == PowerUpType.SPEED_BOOST:
                    text = f"加速: {remaining_sec:.1f}秒"
                    color = (255, 165, 0)  # 橙色
                    icon_color = (255, 165, 0, 200)
                elif power_type == PowerUpType.INVINCIBLE:
                    text = f"无敌: {remaining_sec:.1f}秒"
                    color = (255, 215, 0)  # 金色
                    icon_color = (255, 215, 0, 200)
                elif power_type == PowerUpType.SLOW_MOTION:
                    text = f"慢动作: {remaining_sec:.1f}秒"
                    color = (0, 191, 255)  # 天蓝色
                    icon_color = (0, 191, 255, 200)
                elif power_type == PowerUpType.SMALL_SIZE:
                    text = f"缩小: {remaining_sec:.1f}秒"
                    color = (147, 112, 219)  # 紫色
                    icon_color = (147, 112, 219, 200)
                
                # 创建图标
                icon_size = 12
                icon_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                pygame.draw.circle(icon_surface, icon_color, (icon_size//2, icon_size//2), icon_size//2)
                
                # 添加简单的图标内容
                if power_type == PowerUpType.SPEED_BOOST:
                    # 速度图标 - 箭头
                    pygame.draw.polygon(icon_surface, (255, 255, 255, 220), 
                                       [(3, 6), (9, 3), (9, 9)])
                elif power_type == PowerUpType.INVINCIBLE:
                    # 无敌图标 - 盾牌
                    pygame.draw.polygon(icon_surface, (255, 255, 255, 220), 
                                       [(6, 2), (9, 4), (9, 8), (6, 10), (3, 8), (3, 4)])
                elif power_type == PowerUpType.SLOW_MOTION:
                    # 慢动作图标 - 时钟
                    pygame.draw.circle(icon_surface, (255, 255, 255, 220), (icon_size//2, icon_size//2), 
                                      icon_size//2-2, 1)
                    # 时针
                    pygame.draw.line(icon_surface, (255, 255, 255, 220), 
                                    (icon_size//2, icon_size//2), (icon_size//2, icon_size//2-3), 1)
                    # 分针
                    pygame.draw.line(icon_surface, (255, 255, 255, 220), 
                                    (icon_size//2, icon_size//2), (icon_size//2+2, icon_size//2), 1)
                elif power_type == PowerUpType.SMALL_SIZE:
                    # 缩小图标 - 向内的箭头
                    pygame.draw.line(icon_surface, (255, 255, 255, 220), (3, 3), (6, 6), 1)
                    pygame.draw.line(icon_surface, (255, 255, 255, 220), (9, 3), (6, 6), 1)
                    pygame.draw.line(icon_surface, (255, 255, 255, 220), (3, 9), (6, 6), 1)
                    pygame.draw.line(icon_surface, (255, 255, 255, 220), (9, 9), (6, 6), 1)
                
                # 绘制图标
                self.config.screen.blit(icon_surface, (panel_pos[0] + 5, y_pos + 4))
                
                # 创建文本
                text_surface = effect_font.render(text, True, color)
                text_rect = text_surface.get_rect(midleft=(panel_pos[0] + 20, y_pos + 10))
                
                # 绘制文本
                self.config.screen.blit(text_surface, text_rect)
                
                # 添加进度条 - 更小更简洁
                progress_width = 90
                progress_height = 3
                progress_x = panel_pos[0] + 30
                progress_y = y_pos + 16
                
                # 进度条背景
                pygame.draw.rect(self.config.screen, (50, 50, 50, 150), 
                                (progress_x, progress_y, progress_width, progress_height))
                
                # 计算剩余时间的进度
                progress_percent = remaining_ms / 5000  # 假设所有道具持续5秒
                current_progress = int(progress_width * progress_percent)
                
                # 进度条前景
                pygame.draw.rect(self.config.screen, color, 
                                (progress_x, progress_y, current_progress, progress_height))

    def check_pipe_pass(self):
        """
        检查玩家是否通过管道并更新分数
        """
        # 为每个上管道检查是否通过
        for pipe in self.pipes.upper:
            # 管道中心点
            pipe_centerx = pipe.x + pipe.w/2
            # 检查玩家是否刚刚通过管道中心点
            if (pipe.x < self.player.x < pipe.x + pipe.w) and not hasattr(pipe, 'passed'):
                # 标记该管道已通过
                pipe.passed = True
                # 增加分数
                self.score.add()
                # 播放得分声音
                self.config.sounds.point.play()

    async def play(self):
        """
        主要游戏循环
        """
        # 当玩家开始游戏时
        # 根据游戏模式设置玩家模式
        if self.game_mode == GameMode.REVERSE:
            self.player.set_mode(PlayerMode.REVERSE)  # 设置玩家模式为REVERSE（反向模式）
        elif self.game_mode == GameMode.BOSS:
            self.player.set_mode(PlayerMode.BOSS)  # 设置玩家模式为BOSS（Boss模式）
            self.create_boss()  # 创建初始Boss实体
            
            # 确保每次开始Boss模式时都有足够的准备时间
            self.boss.preparation_time = 120  # 给玩家4秒准备时间
            self.boss.is_preparing = True
            if not hasattr(self.boss, 'initial_preparation_time'):
                self.boss.initial_preparation_time = self.boss.preparation_time
            
            self.pipes.upper.clear()  # 清空管道
            self.pipes.lower.clear()  # 清空管道
        elif self.game_mode == GameMode.COIN:
            self.player.set_mode(PlayerMode.NORMAL)  # 金币模式使用正常玩家模式
            
            # 重置收集的金币数量
            self.collected_coins = 0
            
            # 清空金币管理器
            self.coin_manager.clear()
            
            # 设置金币模式特有的金币生成频率
            self.coin_manager.spawn_rate = 100  # 每100帧生成一枚金币
            self.coin_manager.max_coins = 15    # 最多15枚金币同时存在
        else:
            self.player.set_mode(PlayerMode.NORMAL)  # 设置玩家模式为NORMAL（正常模式）
            
        self.powerup_manager.powerups = []  # 清空道具列表
        self.powerup_manager.active_effects = {}  # 清空活跃效果
        
        # 重置计时器（如果是限时模式）
        if self.game_mode == GameMode.TIMED:
            self.time_remaining = self.time_limit
            
        # 创建字体用于显示剩余时间 - 使用中文字体
        time_font = get_font('SimHei', 24)
        game_over = False
        
        # 添加测试模式提示信息
        test_mode_active = True
        try:
            test_mode_font = get_font('SimHei', 10)  # 更小字体
        except:
            test_mode_font = pygame.font.SysFont('Arial', 10)
        
        # 将测试模式提示分成多行，避免文字拥挤
        test_mode_bg = pygame.Surface((140, 20), pygame.SRCALPHA)  # 更小尺寸
        test_mode_bg.fill((0, 0, 0, 150))  # 半透明黑色背景
        
        # 简化提示文本，减少长度
        test_mode_text = test_mode_font.render("5加速 6无敌 7慢速 8缩小", True, (255, 255, 255))
        
        while True:
            # 计算帧间隔时间
            current_time = pygame.time.get_ticks()
            delta_time = current_time - self.last_frame_time
            self.last_frame_time = current_time

            for event in pygame.event.get():
                self.check_quit_event(event)  # 检查退出事件
                if self.is_tap_event(event):
                    self.player.flap()  # 玩家点击，执行拍打动作
                    # Boss模式下，空格键也用于射击
                    if self.game_mode == GameMode.BOSS:
                        self.player.shoot()
                
                # 添加键盘事件处理
                if event.type == KEYDOWN:
                    # 武器切换 - Q/E键
                    if event.key == K_q and self.game_mode == GameMode.BOSS:
                        self.player.switch_weapon(-1)  # 上一个武器
                    elif event.key == K_e and self.game_mode == GameMode.BOSS:
                        self.player.switch_weapon(1)   # 下一个武器
                    
                    # 数字键1-4直接选择武器
                    if self.game_mode == GameMode.BOSS:
                        if event.key == K_1 and len(self.player.weapons) > 0:
                            self.player.current_weapon_index = 0
                        elif event.key == K_2 and len(self.player.weapons) > 1:
                            self.player.current_weapon_index = 1
                        elif event.key == K_3 and len(self.player.weapons) > 2:
                            self.player.current_weapon_index = 2
                        elif event.key == K_4 and len(self.player.weapons) > 3:
                            self.player.current_weapon_index = 3
                    
                    # 测试模式 - 直接生成特定道具
                    if test_mode_active:
                        if event.key == K_5:  # 5键生成速度道具
                            self.spawn_test_powerup(PowerUpType.SPEED_BOOST)
                        elif event.key == K_6:  # 6键生成无敌道具
                            self.spawn_test_powerup(PowerUpType.INVINCIBLE)
                        elif event.key == K_7:  # 7键生成慢动作道具
                            self.spawn_test_powerup(PowerUpType.SLOW_MOTION)
                        elif event.key == K_8:  # 8键生成缩小道具
                            self.spawn_test_powerup(PowerUpType.SMALL_SIZE)

            # 限时模式时间更新
            if self.game_mode == GameMode.TIMED:
                self.time_remaining -= delta_time
                if self.time_remaining <= 0:
                    self.time_remaining = 0
                    game_over = True
            
            # 更新道具管理器
            self.powerup_manager.tick(delta_time)
            
            # 检查道具碰撞
            self.check_powerup_collisions()
            
            # 更新玩家状态效果
            self.update_player_effects()
            
            # 检查管道通过情况并更新分数（除了Boss模式和金币模式）
            if self.game_mode not in [GameMode.BOSS, GameMode.COIN]:
                self.check_pipe_pass()

            self.background.tick()  # 更新背景
            self.floor.tick()  # 更新地面
            
            # 金币模式特有的逻辑
            if self.game_mode == GameMode.COIN:
                # 更新金币管理器
                self.coin_manager.tick(delta_time)
                
                # 检查金币碰撞并增加分数
                collected_score = self.coin_manager.check_player_collision(self.player)
                if collected_score > 0:
                    # 增加分数
                    for _ in range(collected_score):
                        self.score.add()
                    
                    # 增加收集的金币数量
                    self.collected_coins += collected_score
                
                # 仍然保留管道，但是间隔更大，速度更快，使游戏更具挑战性
                self.pipes.tick()
                
                # 显示金币计数器
                self.render_coin_counter()
            # Boss模式下不渲染管道
            elif self.game_mode != GameMode.BOSS:
                self.pipes.tick()  # 更新管道
                
            self.score.tick()  # 更新得分
            self.player.tick()  # 更新玩家
            
            # Boss模式特有的逻辑
            if self.game_mode == GameMode.BOSS:
                # 更新Boss
                self.boss.tick()
                
                # 设置Boss级别
                self.boss.level = self.boss_cycle + 1
                
                # 之前的状态栏已移除，Boss血条现在直接显示在头上
                
                # 检查玩家子弹是否击中Boss
                if self.player.check_bullet_hit_boss(self.boss):
                    # 增加分数
                    self.score.add()
                    
                # 检查Boss是否被打败，然后进入下一关卡或结束游戏
                if self.boss and self.boss.is_defeated():
                    self.boss_level += 1
                    
                    # 调试输出
                    if hasattr(self.config, 'debug') and self.config.debug:
                        print(f"Boss defeated! Moving to level {self.boss_level}")
                    
                    # 无限循环Boss，无论boss_level多大都会继续
                    # 创建下一个Boss
                    await self.next_boss()
                    # 继续游戏而不是退出游戏循环
                    continue
                
                # 检查玩家是否被Boss子弹击中
                if self.player.check_boss_bullet_collision(self.boss):
                    if not self.player.invincible:
                        return  # 玩家死亡
            
            # 绘制道具
            for powerup in self.powerup_manager.powerups:
                powerup.tick()
                
            # 绘制活跃效果提示
            self.render_active_effects()
            
            # 如果是限时模式，显示剩余时间
            if self.game_mode == GameMode.TIMED:
                seconds_left = max(0, int(self.time_remaining / 1000))
                
                # 创建一个半透明的计时器背景
                timer_bg = pygame.Surface((100, 40), pygame.SRCALPHA)
                alpha = 180  # 透明度
                timer_bg.fill((0, 0, 0, alpha))
                self.config.screen.blit(timer_bg, (self.config.window.width - 110, 5))
                
                # 绘制计时器文本
                time_text = time_font.render(f"时间: {seconds_left}秒", True, (255, 255, 255))
                time_rect = time_text.get_rect(center=(self.config.window.width - 60, 25))
                self.config.screen.blit(time_text, time_rect)
                
                # 当时间小于10秒时闪烁显示并添加红色警告效果
                if seconds_left <= 10 and self.time_remaining > 0:
                    # 闪烁效果
                    if (current_time // 500) % 2 == 0:  # 每500毫秒闪烁一次
                        # 创建警告背景
                        warning_bg = pygame.Surface((200, 40), pygame.SRCALPHA)
                        warning_bg.fill((255, 0, 0, 150))  # 半透明红色
                        warning_rect = warning_bg.get_rect(center=(self.config.window.width//2, 50))
                        self.config.screen.blit(warning_bg, warning_rect)
                        
                        # 警告文本
                        warning_text = time_font.render("时间即将结束！", True, (255, 255, 255))
                        warning_text_rect = warning_text.get_rect(center=(self.config.window.width//2, 50))
                        self.config.screen.blit(warning_text, warning_text_rect)
            
            # 金币模式的提示
            if self.game_mode == GameMode.COIN:
                # 创建一个半透明的提示背景
                coin_tip_bg = pygame.Surface((180, 40), pygame.SRCALPHA)
                coin_tip_bg.fill((0, 0, 0, 150))  # 半透明黑色
                self.config.screen.blit(coin_tip_bg, (5, 5))
                
                # 绘制提示文本
                try:
                    coin_tip_font = get_font('SimHei', 16)  # 尝试使用中文字体
                except:
                    coin_tip_font = pygame.font.SysFont('Arial', 16)  # 如果失败，使用系统字体
                
                coin_tip_text = coin_tip_font.render("收集金币以获得更高分数!", True, (255, 215, 0))
                coin_tip_rect = coin_tip_text.get_rect(center=(95, 25))
                self.config.screen.blit(coin_tip_text, coin_tip_rect)
            
            # 显示测试模式提示
            if test_mode_active:
                # 测试模式提示放在顶部右侧
                bg_rect = pygame.Rect(self.config.window.width - 150, 5, 140, 20)
                
                # 添加边框使其更明显，但更细
                pygame.draw.rect(self.config.screen, (255, 255, 255, 70), bg_rect, 1)
                
                self.config.screen.blit(test_mode_bg, bg_rect)
                # 居中文本
                text_rect = test_mode_text.get_rect(center=(bg_rect.centerx, bg_rect.centery))
                self.config.screen.blit(test_mode_text, text_rect)

            pygame.display.update()  # 刷新显示
            await asyncio.sleep(0)  # 等待下一帧
            self.config.tick()  # 更新游戏配置
            
            # 玩家碰撞检测
            if self.game_mode == GameMode.BOSS:
                # Boss模式下只检测与地板的碰撞
                if (self.player.y + self.player.h >= self.floor.y - 1 or self.player.y < 0) and not self.player.invincible:
                    return
            else:
                # 其他模式下检测与管道和地板的碰撞
                if self.player.collided(self.pipes, self.floor) and not self.player.invincible:
                    return
            
            # 限时模式结束
            if game_over:
                return

    async def game_over(self):
        """
        玩家死亡并显示游戏结束界面
        """
        self.player.set_mode(PlayerMode.CRASH)  # 设置玩家模式为CRASH（死亡模式）
        if hasattr(self, 'pipes') and self.game_mode != GameMode.BOSS:
            self.pipes.stop()  # 停止管道
        if hasattr(self, 'floor'):
            self.floor.stop()  # 停止地面

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)  # 检查退出事件
                if self.is_tap_event(event):
                    if self.player.y + self.player.h >= self.floor.y - 1:
                        return  # 如果玩家落到地面，结束游戏

            self.background.tick()  # 更新背景
            self.floor.tick()  # 更新地面
            
            # Boss模式下不需要更新管道
            if self.game_mode != GameMode.BOSS and hasattr(self, 'pipes'):
                self.pipes.tick()  # 更新管道
                
            self.score.tick()  # 更新得分
            self.player.tick()  # 更新玩家
            self.game_over_message.tick()  # 更新游戏结束信息

            pygame.display.update()  # 刷新显示
            await asyncio.sleep(0)  # 等待下一帧

    def create_boss(self):
        """创建对应等级的Boss"""
        # 取模运算以支持循环Boss
        effective_level = self.boss_level % 4
        
        if effective_level == 0:
            self.boss = Boss(self.config, BossType.NORMAL)
        elif effective_level == 1:
            self.boss = Boss(self.config, BossType.SPEEDY)
        elif effective_level == 2:
            self.boss = Boss(self.config, BossType.SPLITTER)
        elif effective_level == 3:
            self.boss = Boss(self.config, BossType.TANK)
            
        # 记录当前循环次数
        self.boss_cycle = self.boss_level // 4
        
        # 根据循环次数增加Boss难度
        if self.boss_cycle > 0:
            # 每循环一次，增加Boss的最大生命值和当前生命值
            health_increase = self.boss_cycle * 20
            self.boss.max_health += health_increase
            self.boss.health += health_increase
            
            # 减少射击间隔，使Boss更具攻击性
            bullet_rate_decrease = min(self.boss_cycle * 5, 30)  # 最多减少30
            self.boss.bullet_rate = max(self.boss.bullet_rate - bullet_rate_decrease, 10)  # 不少于10
            
            if hasattr(self.config, 'debug') and self.config.debug:
                print(f"Boss cycle {self.boss_cycle}: Health +{health_increase}, Fire rate: {self.boss.bullet_rate}")
                
        # 如果是初始Boss，设置更长的准备时间让玩家熟悉
        if self.boss_level == 0:
            self.boss.preparation_time = 120  # 约4秒，给新玩家更多时间适应
            self.boss.is_preparing = True
    
    def evolve_boss(self):
        """根据得分演化Boss的难度"""
        # 仅当Boss生命低于一定比例时，增加其攻击频率
        if self.boss.health < self.boss.max_health * 0.5:
            if self.boss.boss_type == BossType.NORMAL:
                if self.boss.bullet_rate > 45:  # 不要让它变得太快
                    self.boss.bullet_rate -= 1
                    
            elif self.boss.boss_type == BossType.SPEEDY:
                if self.boss.bullet_rate > 20:
                    self.boss.bullet_rate -= 1
                    
            elif self.boss.boss_type == BossType.SPLITTER:
                if self.boss.bullet_rate > 70:
                    self.boss.bullet_rate -= 1
                    
            elif self.boss.boss_type == BossType.TANK:
                if self.boss.bullet_rate > 100:
                    self.boss.bullet_rate -= 1
    
    async def next_boss(self):
        """显示Boss转场动画并创建下一个Boss"""
        # 清理旧Boss的子弹等资源
        if self.boss:
            self.boss.bullets.clear()
        
        # 创建动画字体 - 使用Arial或系统默认字体
        try:
            font = pygame.font.SysFont('Arial', 36)
        except:
            font = pygame.font.Font(None, 36)
        
        # 计算有效的Boss等级
        effective_level = self.boss_level % 4
        cycle_count = self.boss_level // 4
        
        # 根据下一个Boss类型显示文本
        if effective_level == 0:
            boss_name = "Normal Boss"
            color = (255, 0, 0)  # 红色
        elif effective_level == 1:
            boss_name = "Speed Boss"
            color = (0, 0, 255)  # 蓝色
        elif effective_level == 2:
            boss_name = "Splitter Boss"
            color = (0, 255, 0)  # 绿色
        elif effective_level == 3:
            boss_name = "Tank Boss"
            color = (128, 0, 128)  # 紫色
        
        # 添加循环次数信息
        if cycle_count > 0:
            text = font.render(f"{boss_name} Lv.{cycle_count+1} Appears!", True, color)
        else:
            text = font.render(f"{boss_name} Appears!", True, color)
        
        rect = text.get_rect(center=(self.config.window.width//2, self.config.window.height//2))
        
        # 确保玩家不会掉落 - 重置位置到中心
        self.player.y = self.config.window.height // 2 - self.player.h // 2
        self.player.vel_y = 0  # 重置速度，防止继续掉落
        
        # 显示过渡动画
        for i in range(60):  # 约2秒
            # 绘制游戏元素
            self.background.tick()
            self.floor.tick()
            
            # 确保玩家留在屏幕中心
            self.player.y = self.config.window.height // 2 - self.player.h // 2
            self.player.tick()
            
            # 添加半透明背景
            overlay = pygame.Surface((self.config.window.width, self.config.window.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.config.screen.blit(overlay, (0, 0))
            
            # 绘制文本
            self.config.screen.blit(text, rect)
            
            pygame.display.update()
            await asyncio.sleep(0.03)
        
        # 创建新Boss
        self.create_boss()
        
        # 为不同类型的Boss设置不同的准备时间
        if effective_level == 0:  # 普通Boss
            self.boss.preparation_time = 60  # 约2秒
        elif effective_level == 1:  # 速度Boss
            self.boss.preparation_time = 90  # 约3秒 (速度快，给玩家更多准备时间)
        elif effective_level == 2:  # 分裂Boss
            self.boss.preparation_time = 75  # 约2.5秒
        elif effective_level == 3:  # 坦克Boss
            self.boss.preparation_time = 45  # 约1.5秒 (移动慢，准备时间短)
            
        # 确保准备阶段标志被重置
        self.boss.is_preparing = True
        
        # 重置玩家状态
        self.player.bullets.clear()  # 清除玩家所有未命中的子弹
        
        # 更新玩家 - 恢复一些武器弹药并给予额外奖励
        for weapon in self.player.weapons:
            if weapon.weapon_type == WeaponType.TRIPLE and weapon.ammo < 15:
                weapon.ammo = 15
            elif weapon.weapon_type == WeaponType.LASER and weapon.ammo < 50:
                weapon.ammo = 50
            elif weapon.weapon_type == WeaponType.HOMING and weapon.ammo < 5:
                weapon.ammo = 5

    def spawn_test_powerup(self, power_type):
        """测试功能：在玩家前方生成特定类型的道具"""
        # 在玩家前方位置生成
        x = self.player.x + 100  # 在玩家前方100像素处
        y = self.player.y  # 与玩家相同的高度
        
        # 创建道具并添加到列表
        powerup = PowerUp(self.config, power_type, x, y)
        self.powerup_manager.powerups.append(powerup)
        
        # 可选：播放提示音效
        self.config.sounds.swoosh.play()

    def render_coin_counter(self):
        """
        在金币模式下显示金币计数器
        """
        # 创建一个半透明的背景
        counter_bg = pygame.Surface((120, 40), pygame.SRCALPHA)
        counter_bg.fill((0, 0, 0, 150))  # 半透明黑色
        
        # 位置放在屏幕下方
        bg_pos = (self.config.window.width // 2 - 60, self.floor.y - 50)
        self.config.screen.blit(counter_bg, bg_pos)
        
        # 绘制金币图标
        coin_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(coin_icon, (255, 215, 0), (15, 15), 15)  # 金色圆形
        pygame.draw.circle(coin_icon, (255, 235, 100), (15, 15), 10)  # 浅金色内圈
        
        # 添加 "$" 符号
        try:
            coin_font = pygame.font.SysFont("Arial", 16, bold=True)
        except:
            coin_font = pygame.font.Font(None, 16)
        coin_symbol = coin_font.render("$", True, (100, 80, 0))
        symbol_rect = coin_symbol.get_rect(center=(15, 15))
        coin_icon.blit(coin_symbol, symbol_rect)
        
        # 绘制金币图标
        self.config.screen.blit(coin_icon, (bg_pos[0] + 10, bg_pos[1] + 5))
        
        # 绘制收集的金币数量
        try:
            counter_font = get_font('SimHei', 18)
        except:
            counter_font = pygame.font.SysFont('Arial', 18)
        
        counter_text = counter_font.render(f"x {self.collected_coins}", True, (255, 215, 0))
        text_pos = (bg_pos[0] + 45, bg_pos[1] + 20)
        self.config.screen.blit(counter_text, text_pos)

    def render_boss_status(self):
        """绘制Boss状态栏，显示Boss血量和关卡信息 - 已废弃，现在直接显示在Boss头顶"""
        pass  # 此功能已移至Boss实体类中的draw_health_bar_overhead方法
