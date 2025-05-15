import random
import pygame
from enum import Enum
from typing import List

from .entity import Entity
from ..utils import GameConfig


class CoinType(Enum):
    """金币类型枚举"""
    BRONZE = "铜币"    # 铜币，1分
    SILVER = "银币"    # 银币，3分
    GOLD = "金币"      # 金币，5分


class Coin(Entity):
    """金币实体类"""
    
    def __init__(self, config: GameConfig, coin_type: CoinType = CoinType.BRONZE, x: int = 0, y: int = 0) -> None:
        """初始化金币实体
        
        Args:
            config: 游戏配置
            coin_type: 金币类型，默认为铜币
            x: 初始x坐标
            y: 初始y坐标
        """
        self.coin_type = coin_type
        self.config = config
        
        # 金币属性设置
        self.coin_size = 25  # 金币大小
        self.velocity = -4   # 金币移动速度
        self.rotation_angle = 0  # 旋转角度
        self.rotation_speed = 2  # 旋转速度
        self.active = True  # 是否激活
        
        # 根据类型设置金币颜色和分值
        if coin_type == CoinType.BRONZE:
            self.color = (184, 115, 51)  # 铜色
            self.score_value = 1
        elif coin_type == CoinType.SILVER:
            self.color = (192, 192, 192)  # 银色
            self.score_value = 3
        elif coin_type == CoinType.GOLD:
            self.color = (255, 215, 0)  # 金色
            self.score_value = 5
        
        # 创建金币表面
        coin_surface = self.create_coin_surface()
        
        # 调用父类初始化
        super().__init__(config, coin_surface, x, y)
    
    def create_coin_surface(self) -> pygame.Surface:
        """创建金币表面"""
        # 创建圆形金币
        surface = pygame.Surface((self.coin_size, self.coin_size), pygame.SRCALPHA)
        
        # 外圈
        pygame.draw.circle(surface, self.color, (self.coin_size//2, self.coin_size//2), self.coin_size//2)
        
        # 内圈（淡色）
        inner_color = self.lighten_color(self.color, 50)
        pygame.draw.circle(surface, inner_color, (self.coin_size//2, self.coin_size//2), self.coin_size//2 - 4)
        
        # 中心点
        center_color = self.lighten_color(self.color, 100)
        pygame.draw.circle(surface, center_color, (self.coin_size//2, self.coin_size//2), self.coin_size//4)
        
        # 金币类型标记
        if self.coin_type == CoinType.BRONZE:
            # 铜币：B
            self.draw_text(surface, "B")
        elif self.coin_type == CoinType.SILVER:
            # 银币：S
            self.draw_text(surface, "S")
        elif self.coin_type == CoinType.GOLD:
            # 金币：G
            self.draw_text(surface, "G")
        
        return surface
    
    def draw_text(self, surface: pygame.Surface, text: str) -> None:
        """在金币上绘制文字"""
        try:
            # 尝试使用Arial字体
            font = pygame.font.SysFont("Arial", 12, bold=True)
        except:
            # 如果失败，使用默认字体
            font = pygame.font.Font(None, 12)
        
        # 创建文本
        text_surface = font.render(text, True, (50, 50, 50))
        text_rect = text_surface.get_rect(center=(self.coin_size//2, self.coin_size//2))
        
        # 绘制到表面
        surface.blit(text_surface, text_rect)
    
    def lighten_color(self, color: tuple, amount: int) -> tuple:
        """使颜色变亮"""
        r, g, b = color
        return (min(r + amount, 255), min(g + amount, 255), min(b + amount, 255))
    
    def tick(self) -> None:
        """更新金币状态"""
        if not self.active:
            return
        
        # 移动金币
        self.x += self.velocity
        
        # 旋转金币
        self.rotation_angle = (self.rotation_angle + self.rotation_speed) % 360
        rotated_image = pygame.transform.rotate(self.image, self.rotation_angle)
        
        # 获取旋转后的矩形，并保持中心点不变
        rect = rotated_image.get_rect(center=(self.x + self.w//2, self.y + self.h//2))
        
        # 绘制金币
        self.config.screen.blit(rotated_image, rect.topleft)
        
        # 检查是否超出屏幕
        if self.x + self.coin_size < 0:
            self.active = False
    
    def is_active(self) -> bool:
        """检查金币是否激活"""
        return self.active
    
    def collect(self) -> int:
        """收集金币，返回分值"""
        self.active = False
        return self.score_value


class CoinManager:
    """金币管理器类"""
    
    def __init__(self, config: GameConfig) -> None:
        """初始化金币管理器
        
        Args:
            config: 游戏配置
        """
        self.config = config
        self.coins: List[Coin] = []  # 金币列表
        
        # 生成参数
        self.spawn_rate = 120  # 生成间隔（帧数）
        self.spawn_timer = 0   # 生成计时器
        self.max_coins = 10    # 最大金币数量
        
        # 概率设置
        self.bronze_chance = 0.6  # 铜币概率
        self.silver_chance = 0.3  # 银币概率
        self.gold_chance = 0.1    # 金币概率
    
    def tick(self, delta_time: int) -> None:
        """更新金币管理器状态
        
        Args:
            delta_time: 帧间隔时间
        """
        # 更新金币生成计时器
        self.spawn_timer += 1
        
        # 检查是否应该生成新金币
        if self.spawn_timer >= self.spawn_rate and len(self.coins) < self.max_coins:
            self.spawn_coin()
            self.spawn_timer = 0
        
        # 更新并绘制所有金币
        active_coins = []
        for coin in self.coins:
            if coin.is_active():
                coin.tick()
                active_coins.append(coin)
        
        # 更新金币列表，清除已失活的金币
        self.coins = active_coins
    
    def spawn_coin(self) -> None:
        """生成新金币"""
        # 随机位置（在屏幕右侧，垂直位置随机）
        x = self.config.window.width
        y = random.randint(50, self.config.window.height - 100)
        
        # 根据概率选择金币类型
        coin_type_rand = random.random()
        if coin_type_rand < self.bronze_chance:
            coin_type = CoinType.BRONZE
        elif coin_type_rand < self.bronze_chance + self.silver_chance:
            coin_type = CoinType.SILVER
        else:
            coin_type = CoinType.GOLD
        
        # 创建金币并添加到列表
        coin = Coin(self.config, coin_type, x, y)
        self.coins.append(coin)
    
    def check_player_collision(self, player) -> int:
        """检查玩家与金币的碰撞，返回获得的分数
        
        Args:
            player: 玩家实体
        
        Returns:
            int: 获得的分数
        """
        score = 0
        coins_to_remove = []
        
        for coin in self.coins:
            if coin.is_active() and player.collide(coin):
                # 收集金币并获得分数
                score += coin.collect()
                coins_to_remove.append(coin)
                
                # 播放得分音效
                self.config.sounds.point.play()
        
        # 移除已收集的金币
        for coin in coins_to_remove:
            if coin in self.coins:
                self.coins.remove(coin)
        
        return score
    
    def clear(self) -> None:
        """清空所有金币"""
        self.coins.clear()
        self.spawn_timer = 0 