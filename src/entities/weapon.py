from enum import Enum
import pygame
import math
from typing import List, Optional

from ..utils import GameConfig
from .bullet import Bullet
from .boss import Boss

class WeaponType(Enum):
    """武器类型枚举"""
    NORMAL = "基础子弹"    # 基础单发子弹
    TRIPLE = "三连发"      # 三连发子弹
    LASER = "激光"        # 持续性激光
    HOMING = "追踪导弹"      # 追踪敌人的子弹

class Weapon:
    def __init__(self, config: GameConfig, weapon_type: WeaponType = WeaponType.NORMAL):
        self.config = config
        self.weapon_type = weapon_type
        
        # 设置武器属性
        if weapon_type == WeaponType.NORMAL:
            self.cooldown = 15       # 发射冷却时间
            self.damage = 10         # 伤害值
            self.ammo = -1           # 无限弹药
            self.color = (255, 255, 0)  # 黄色
            
        elif weapon_type == WeaponType.TRIPLE:
            self.cooldown = 25
            self.damage = 5
            self.ammo = 30           # 有限弹药
            self.color = (0, 255, 255)  # 青色
            
        elif weapon_type == WeaponType.LASER:
            self.cooldown = 5
            self.damage = 2          # 每帧伤害
            self.ammo = 100          # 能量值
            self.color = (255, 0, 255)  # 粉色
            self.is_firing = False
            self.laser_width = 3     # 激光宽度
            self.laser_max_length = 1000  # 最大长度
            
        elif weapon_type == WeaponType.HOMING:
            self.cooldown = 45
            self.damage = 15
            self.ammo = 10
            self.color = (255, 128, 0)  # 橙色
            self.homing_speed = 7    # 追踪速度
            self.turn_rate = 0.15    # 转向速率
            
        self.current_cooldown = 0
        
    def update(self) -> None:
        """更新武器状态"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
            
    def can_fire(self) -> bool:
        """检查是否可以开火"""
        if self.current_cooldown > 0:
            return False
            
        if self.ammo == 0:
            return False
            
        return True
        
    def fire(self, x: int, y: int, target: Optional[Boss] = None) -> List[Bullet]:
        """开火并返回生成的子弹列表"""
        if not self.can_fire():
            return []
            
        # 重置冷却时间
        self.current_cooldown = self.cooldown
        
        # 如果有限弹药，减少弹药数
        if self.ammo > 0:
            self.ammo -= 1
            
        bullets = []
        
        # 根据武器类型创建不同的子弹
        if self.weapon_type == WeaponType.NORMAL:
            bullets.append(self.create_normal_bullet(x, y))
            
        elif self.weapon_type == WeaponType.TRIPLE:
            bullets.extend(self.create_triple_bullets(x, y))
            
        elif self.weapon_type == WeaponType.LASER:
            bullets.append(self.create_laser_bullet(x, y))
            
        elif self.weapon_type == WeaponType.HOMING:
            bullets.append(self.create_homing_bullet(x, y, target))
            
        # 播放声音
        self.config.sounds.swoosh.play()
        
        return bullets
        
    def create_normal_bullet(self, x: int, y: int) -> Bullet:
        """创建普通子弹"""
        bullet = Bullet(self.config, x, y)
        bullet.damage = self.damage
        bullet.vel_x = 10  # 向右飞行
        
        # 自定义外观
        size = 8
        bullet_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(bullet_surface, self.color, (size//2, size//2), size//2)
        bullet.image = bullet_surface
        
        return bullet
        
    def create_triple_bullets(self, x: int, y: int) -> List[Bullet]:
        """创建三连发子弹"""
        bullets = []
        angles = [-15, 0, 15]  # 发射角度
        
        for angle in angles:
            bullet = Bullet(self.config, x, y)
            bullet.damage = self.damage
            
            # 计算速度分量
            angle_rad = math.radians(angle)
            bullet.vel_x = 10 * math.cos(angle_rad)
            bullet.vel_y = 10 * math.sin(angle_rad)
            
            # 自定义外观
            size = 6  # 略小的子弹
            bullet_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(bullet_surface, self.color, (size//2, size//2), size//2)
            bullet.image = bullet_surface
            
            bullets.append(bullet)
            
        return bullets
        
    def create_laser_bullet(self, x: int, y: int) -> Bullet:
        """创建激光子弹"""
        # 创建一个特殊的激光子弹
        bullet = Bullet(self.config, x, y)
        bullet.damage = self.damage
        bullet.vel_x = 20  # 非常快的速度
        bullet.is_laser = True
        
        # 自定义外观 - 细长的矩形
        width = 20
        height = self.laser_width
        laser_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(laser_surface, self.color, (0, 0, width, height))
        
        # 添加发光效果
        glow_surface = pygame.Surface((width+4, height+4), pygame.SRCALPHA)
        glow_color = (*self.color, 100)  # 半透明的颜色
        pygame.draw.rect(glow_surface, glow_color, (0, 0, width+4, height+4))
        
        # 合并图层
        final_surface = pygame.Surface((width+4, height+4), pygame.SRCALPHA)
        final_surface.blit(glow_surface, (0, 0))
        final_surface.blit(laser_surface, (2, 2))  # 居中放置
        
        bullet.image = final_surface
        bullet.trail_length = 3  # 激光拖尾效果
        bullet.trail_frames = []  # 存储拖尾帧
        
        return bullet
        
    def create_homing_bullet(self, x: int, y: int, target: Optional[Boss]) -> Bullet:
        """创建追踪子弹"""
        bullet = Bullet(self.config, x, y)
        bullet.damage = self.damage
        bullet.vel_x = 5  # 初始速度
        bullet.vel_y = 0
        bullet.speed = self.homing_speed
        bullet.turn_rate = self.turn_rate
        bullet.target = target  # 存储目标引用
        bullet.is_homing = True
        
        # 自定义外观 - 小火箭形状
        size = 12
        rocket_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # 绘制火箭头部
        pygame.draw.circle(rocket_surface, self.color, (size-3, size//2), 4)
        
        # 绘制火箭主体
        pygame.draw.rect(rocket_surface, self.color, (2, size//2-2, size-5, 4))
        
        # 绘制小尾翼
        pygame.draw.polygon(rocket_surface, self.color, [
            (0, size//2-3), (4, size//2), (0, size//2+3)
        ])
        
        # 添加发光效果
        glow_surface = pygame.Surface((size+6, size+6), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color, 100), (size+3, size//2+3), 6)
        
        # 合并图层
        final_surface = pygame.Surface((size+6, size+6), pygame.SRCALPHA)
        final_surface.blit(glow_surface, (0, 0))
        final_surface.blit(rocket_surface, (3, 3))
        
        bullet.image = final_surface
        bullet.update_homing = self.update_homing_bullet  # 添加特殊的更新方法
        
        return bullet
        
    def update_homing_bullet(self, bullet) -> None:
        """更新追踪子弹的轨迹"""
        if not bullet.target or not hasattr(bullet.target, 'x'):
            # 如果没有目标，就直线飞行
            bullet.x += bullet.vel_x
            bullet.y += bullet.vel_y
            return
            
        # 计算子弹到目标的方向
        target_x = bullet.target.x + bullet.target.w // 2
        target_y = bullet.target.y + bullet.target.h // 2
        
        dx = target_x - bullet.x
        dy = target_y - bullet.y
        angle = math.atan2(dy, dx)
        
        # 计算当前速度的角度
        current_angle = math.atan2(bullet.vel_y, bullet.vel_x)
        
        # 计算角度差，限制在-π到π之间
        angle_diff = (angle - current_angle + math.pi) % (2 * math.pi) - math.pi
        
        # 根据转向速率调整当前角度
        current_angle += angle_diff * bullet.turn_rate
        
        # 更新速度
        bullet.vel_x = bullet.speed * math.cos(current_angle)
        bullet.vel_y = bullet.speed * math.sin(current_angle)
        
        # 应用速度
        bullet.x += bullet.vel_x
        bullet.y += bullet.vel_y
        
        # 旋转子弹精灵以面向移动方向
        angle_degrees = math.degrees(current_angle)
        bullet.image = pygame.transform.rotate(bullet.original_image, -angle_degrees) 