import random
from enum import Enum
from typing import Optional
import math

import pygame

from ..utils import GameConfig
from .entity import Entity


class PowerUpType(Enum):
    """道具类型枚举"""
    SPEED_BOOST = "SPEED_BOOST"  # 加速
    INVINCIBLE = "INVINCIBLE"    # 无敌
    SLOW_MOTION = "SLOW_MOTION"  # 慢动作
    SMALL_SIZE = "SMALL_SIZE"    # 缩小玩家


class PowerUp(Entity):
    """道具实体类"""
    def __init__(self, config: GameConfig, power_type: PowerUpType, x: int, y: int) -> None:
        self.config = config
        self.power_type = power_type
        
        # 根据道具类型选择主要和次要颜色
        color_map = {
            PowerUpType.SPEED_BOOST: [(255, 165, 0), (255, 140, 0)],   # 橙色系
            PowerUpType.INVINCIBLE: [(255, 215, 0), (255, 240, 60)],   # 金色系
            PowerUpType.SLOW_MOTION: [(0, 191, 255), (30, 144, 255)],  # 蓝色系
            PowerUpType.SMALL_SIZE: [(147, 112, 219), (138, 43, 226)], # 紫色系
        }
        
        # 设置道具基本属性
        self.primary_color = color_map[power_type][0]
        self.secondary_color = color_map[power_type][1]
        
        # 根据道具类型设置持续时间
        duration_map = {
            PowerUpType.SPEED_BOOST: 8000,    # 8秒
            PowerUpType.INVINCIBLE: 10000,    # 10秒
            PowerUpType.SLOW_MOTION: 8000,    # 8秒
            PowerUpType.SMALL_SIZE: 8000,     # 8秒
        }
        self.duration = duration_map[power_type]  # 道具持续时间(毫秒)
        
        self.vel_x = -4  # 水平移动速度
        
        # 创建更精美的道具图像
        size = 32  # 略微增大尺寸
        
        # 创建主表面
        main_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # 绘制道具图标
        self.draw_powerup_icon(main_surface, power_type, size)
        
        # 添加外部光环效果
        glow_size = size + 12
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        # 绘制多层次的辉光效果
        for radius in range(glow_size//2, glow_size//2-4, -1):
            alpha = 40 + (glow_size//2 - radius) * 20
            pygame.draw.circle(
                glow_surface, 
                (*self.primary_color, min(alpha, 120)), 
                (glow_size//2, glow_size//2), 
                radius
            )
        
        # 合并图层
        final_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        final_surface.blit(glow_surface, (0, 0))
        final_surface.blit(main_surface, ((glow_size - size) // 2, (glow_size - size) // 2))
        
        super().__init__(config, final_surface, x, y)
        
        # 动画参数
        self.animation_tick = 0
        self.rotation_angle = 0  # 旋转角度
        self.pulse_scale = 1.0
        self.pulse_direction = 0.01
        self.original_image = self.image.copy()  # 保存原始图像用于动画
        self.shine_angle = 0  # 闪光效果角度
        
        # 保存中心坐标
        self.center_x = self.x + self.w / 2
        self.center_y = self.y + self.h / 2
    
    def draw_powerup_icon(self, surface, power_type, size):
        """根据不同道具类型绘制不同图标"""
        center = size // 2
        radius = size // 2 - 2
        
        # 首先绘制基础圆形
        pygame.draw.circle(surface, self.primary_color, (center, center), radius)
        
        # 内部渐变效果
        for i in range(5):
            inner_radius = radius - 2 - i
            if inner_radius > 0:
                pygame.draw.circle(
                    surface, 
                    self.secondary_color,
                    (center, center), 
                    inner_radius
                )
        
        # 根据道具类型绘制不同的图标
        if power_type == PowerUpType.SPEED_BOOST:
            # 速度提升 - 双箭头图标
            arrow_width = size // 3
            arrow_height = size // 2
            arrow_color = (255, 255, 255, 230)
            
            # 第一个箭头
            points1 = [
                (center - arrow_width//2, center + arrow_height//3),
                (center, center - arrow_height//3),
                (center + arrow_width//2, center + arrow_height//3)
            ]
            # 第二个箭头（在下方）
            points2 = [
                (center - arrow_width//2, center),
                (center, center - arrow_height//3 * 2),
                (center + arrow_width//2, center)
            ]
            
            pygame.draw.polygon(surface, arrow_color, points1)
            pygame.draw.polygon(surface, arrow_color, points2)
            
        elif power_type == PowerUpType.INVINCIBLE:
            # 无敌 - 盾牌图标
            shield_color = (255, 255, 255, 230)
            
            # 绘制盾牌外形
            shield_width = size // 2
            shield_height = size // 2
            shield_top = center - shield_height//2
            shield_left = center - shield_width//2
            
            # 盾牌主体
            points = [
                (center, shield_top),
                (center + shield_width//2, shield_top + shield_height//4),
                (center + shield_width//2, shield_top + shield_height//4*3),
                (center, shield_top + shield_height),
                (center - shield_width//2, shield_top + shield_height//4*3),
                (center - shield_width//2, shield_top + shield_height//4),
            ]
            pygame.draw.polygon(surface, shield_color, points)
            
            # 盾牌内部装饰
            small_radius = radius // 3
            pygame.draw.circle(surface, self.primary_color, (center, center), small_radius)
            pygame.draw.circle(surface, shield_color, (center, center), small_radius, 1)
            
        elif power_type == PowerUpType.SLOW_MOTION:
            # 慢动作 - 时钟图标
            clock_color = (255, 255, 255, 230)
            clock_radius = radius * 0.7
            
            # 时钟外圈
            pygame.draw.circle(surface, clock_color, (center, center), clock_radius, 2)
            
            # 时钟指针
            # 时针
            hour_angle = math.pi / 4
            hour_length = clock_radius * 0.5
            hour_end_x = center + hour_length * math.sin(hour_angle)
            hour_end_y = center - hour_length * math.cos(hour_angle)
            pygame.draw.line(surface, clock_color, (center, center), (hour_end_x, hour_end_y), 2)
            
            # 分针
            minute_angle = math.pi * 3 / 4
            minute_length = clock_radius * 0.7
            minute_end_x = center + minute_length * math.sin(minute_angle)
            minute_end_y = center - minute_length * math.cos(minute_angle)
            pygame.draw.line(surface, clock_color, (center, center), (minute_end_x, minute_end_y), 2)
            
            # 时钟中心点
            pygame.draw.circle(surface, clock_color, (center, center), 2)
            
        elif power_type == PowerUpType.SMALL_SIZE:
            # 缩小 - 缩小图标
            arrow_color = (255, 255, 255, 230)
            arrow_size = radius * 0.7
            
            # 向内的箭头
            for angle in [0, math.pi/2, math.pi, math.pi*3/2]:
                start_x = center + arrow_size * math.cos(angle)
                start_y = center + arrow_size * math.sin(angle)
                end_x = center + arrow_size * 0.4 * math.cos(angle)
                end_y = center + arrow_size * 0.4 * math.sin(angle)
                
                # 箭头线
                pygame.draw.line(surface, arrow_color, (start_x, start_y), (end_x, end_y), 2)
                
                # 箭头头部
                head_size = 4
                head_angle1 = angle + math.pi/4
                head_angle2 = angle - math.pi/4
                head1_x = start_x + head_size * math.cos(head_angle1)
                head1_y = start_y + head_size * math.sin(head_angle1)
                head2_x = start_x + head_size * math.cos(head_angle2)
                head2_y = start_y + head_size * math.sin(head_angle2)
                
                pygame.draw.line(surface, arrow_color, (start_x, start_y), (head1_x, head1_y), 2)
                pygame.draw.line(surface, arrow_color, (start_x, start_y), (head2_x, head2_y), 2)
            
            # 中心小圆
            pygame.draw.circle(surface, arrow_color, (center, center), 3)
    
    def draw(self) -> None:
        self.x += self.vel_x  # 更新位置
        # 更新中心坐标
        self.center_x = self.x + self.w / 2
        self.center_y = self.y + self.h / 2
        self.animate()  # 更新动画
        super().draw()  # 调用父类绘制方法
    
    def animate(self) -> None:
        """使道具产生更丰富的动画效果"""
        self.animation_tick += 1
        
        # 旋转效果 - 根据道具类型决定是否旋转以及旋转速度
        rotation_speed = {
            PowerUpType.SPEED_BOOST: 0.5,
            PowerUpType.INVINCIBLE: 0.2,
            PowerUpType.SLOW_MOTION: 0.3,
            PowerUpType.SMALL_SIZE: 0.4
        }.get(self.power_type, 0)
        
        self.rotation_angle = (self.rotation_angle + rotation_speed) % 360
        
        # 光晕闪烁效果
        self.shine_angle = (self.shine_angle + 2) % 360
        shine_intensity = (math.sin(math.radians(self.shine_angle)) + 1) / 2  # 0到1之间变化
        
        # 脉动效果，每3帧更新一次
        if self.animation_tick % 3 == 0:
            self.pulse_scale += self.pulse_direction
            if self.pulse_scale > 1.08:
                self.pulse_direction = -0.01
            elif self.pulse_scale < 0.92:
                self.pulse_direction = 0.01
        
        # 应用所有动画效果创建新图像
        scaled_size = int(self.original_image.get_width() * self.pulse_scale)
        
        # 先缩放原始图像
        scaled_image = pygame.transform.scale(self.original_image, (scaled_size, scaled_size))
        
        # 然后旋转图像
        if rotation_speed > 0:
            rotated_image = pygame.transform.rotate(scaled_image, self.rotation_angle)
        else:
            rotated_image = scaled_image
        
        # 更新图像和尺寸
        self.image = rotated_image
        self.w = self.image.get_width()
        self.h = self.image.get_height()
        
        # 更新位置以保持中心不变
        self.x = self.center_x - self.w / 2
        self.y = self.center_y - self.h / 2


class PowerUpManager:
    """道具管理器，负责道具的生成、更新和移除"""
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.powerups = []
        self.spawn_timer = 0
        self.spawn_interval = 1500  # 从3000ms减少到1500ms，每1.5秒生成一次道具的机会
        self.spawn_chance = 0.9     # 从0.6增加到0.9，90%概率生成道具
        self.active_effects = {}    # 当前激活的效果 {PowerUpType: end_time}
    
    def tick(self, delta_time: int) -> None:
        """更新所有道具状态"""
        # 更新生成计时器
        self.spawn_timer += delta_time
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            if random.random() < self.spawn_chance:
                # 有概率同时生成多个道具
                num_powerups = 1
                if random.random() < 0.4:  # 40%的概率生成多个道具
                    num_powerups = random.randint(2, 3)  # 生成2-3个道具
                
                for _ in range(num_powerups):
                    self.spawn_powerup()
        
        # 更新和移除道具
        for powerup in list(self.powerups):
            powerup.tick()
            # 移除超出屏幕的道具
            if powerup.x < -powerup.w:
                self.powerups.remove(powerup)
        
        # 更新激活效果的剩余时间
        current_time = pygame.time.get_ticks()
        expired_effects = []
        
        for effect_type, end_time in self.active_effects.items():
            if current_time >= end_time:
                expired_effects.append(effect_type)
                
        # 移除过期效果
        for effect in expired_effects:
            self.active_effects.pop(effect)
    
    def spawn_powerup(self) -> None:
        """生成一个随机道具"""
        # 从枚举中随机选择一个道具类型
        power_type = random.choice(list(PowerUpType))
        
        # 在合适的位置生成道具
        x = self.config.window.width + 10
        # 在屏幕中央区域随机生成
        min_y = int(self.config.window.height * 0.2)
        max_y = int(self.config.window.height * 0.7)
        y = random.randint(min_y, max_y)
        
        # 创建道具并添加到列表
        powerup = PowerUp(self.config, power_type, x, y)
        self.powerups.append(powerup)
    
    def activate_effect(self, power_type: PowerUpType) -> None:
        """激活道具效果"""
        current_time = pygame.time.get_ticks()
        # 使用临时道具对象获取持续时间，避免创建完整的道具实例
        temp_powerup = PowerUp(self.config, power_type, 0, 0)
        end_time = current_time + temp_powerup.duration
        self.active_effects[power_type] = end_time
        
        # 为不同道具播放不同音效
        if power_type == PowerUpType.SPEED_BOOST:
            # 加速音效 - 使用point音效，但设置频率更高
            self.config.sounds.point.set_volume(0.8)
            self.config.sounds.point.play()
            # 连续播放两次来表示加速感
            pygame.time.delay(100)
            self.config.sounds.point.play()
            # 恢复音量
            pygame.time.delay(50)
            self.config.sounds.point.set_volume(1.0)
        elif power_type == PowerUpType.INVINCIBLE:
            # 无敌音效 - 使用wing音效，但通过设置频率来获得更金属的感觉
            self.config.sounds.wing.set_volume(1.2)  # 音量稍微提高
            self.config.sounds.wing.play()
            # 延迟一点后播放point音效增强无敌获得的感觉
            pygame.time.delay(150)
            self.config.sounds.point.play()
            # 恢复音量
            pygame.time.delay(50)
            self.config.sounds.wing.set_volume(1.0)
        elif power_type == PowerUpType.SLOW_MOTION:
            # 慢动作音效 - 使用swoosh音效，较低的音调
            self.config.sounds.swoosh.set_volume(0.7)
            self.config.sounds.swoosh.play()
            # 恢复音量
            pygame.time.delay(100)
            self.config.sounds.swoosh.set_volume(1.0)
        elif power_type == PowerUpType.SMALL_SIZE:
            # 缩小音效 - 使用point和swoosh的组合
            self.config.sounds.swoosh.set_volume(0.6)
            self.config.sounds.swoosh.play()
            pygame.time.delay(50)
            self.config.sounds.point.set_volume(0.6)
            self.config.sounds.point.play()
            # 恢复音量
            pygame.time.delay(50)
            self.config.sounds.swoosh.set_volume(1.0)
            self.config.sounds.point.set_volume(1.0)
    
    def has_effect(self, power_type: PowerUpType) -> bool:
        """检查指定的效果是否处于激活状态"""
        return power_type in self.active_effects
    
    def get_remaining_time(self, power_type: PowerUpType) -> Optional[int]:
        """获取效果剩余时间"""
        if not self.has_effect(power_type):
            return None
        
        current_time = pygame.time.get_ticks()
        end_time = self.active_effects[power_type]
        return max(0, end_time - current_time)
