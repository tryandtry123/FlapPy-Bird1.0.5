from enum import Enum
from itertools import cycle
from typing import List
import math
import random

import pygame

from ..utils import GameConfig, clamp, get_font
from .entity import Entity
from .floor import Floor
from .pipe import Pipe, Pipes
from .powerup import PowerUpType
from .bullet import Bullet
from .weapon import Weapon, WeaponType


class PlayerMode(Enum):
    """玩家模式枚举"""
    NORMAL = "NORMAL"  # 正常模式
    SHM = "SHM"  # 静止模式
    CRASH = "CRASH"  # 撞击模式
    CRASHED = "CRASHED"  # 撞击模式
    REVERSE = "REVERSE"  # 反向模式
    BOSS = "BOSS"  # Boss模式


class Player(Entity):
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        images = config.images.player  # 获取玩家图像

        # 根据模式设置当前图像
        x = int(config.window.width * 0.2)
        y = int((config.window.height - images[0].get_height()) / 2)

        super().__init__(config, images[0], x, y)  # 初始化父类

        # 设置碰撞的管道或地板
        self.crash_entity = None

        # 生成用于显示图像的索引
        self.img_gen = self.generate_index()
        next(self.img_gen)  # 初始化索引

        # 速度修改器
        self.speed_modifier = 1.0
        self.size_modifier = 1.0  # 大小修改器
        
        # 子弹
        self.bullets = []
        self.bullet_damage = 10  # 默认伤害值
        self.invincible = False  # 是否无敌
        
        # 武器系统
        self.weapons = [
            Weapon(config, WeaponType.NORMAL),
            Weapon(config, WeaponType.TRIPLE),
            Weapon(config, WeaponType.LASER),
            Weapon(config, WeaponType.HOMING)
        ]
        self.current_weapon_index = 0
        self.bullet_rate = 15  # 子弹发射冷却时间
        self.bullet_cooldown = 0  # 当前冷却计时器
        
        # 爆炸特效
        self.explosions = []
        
        # 添加弹药显示 - 位置调整到右下角，但与边缘保持适当距离
        self.bullet_ui_pos = (config.window.width - 120, config.window.height - 60)

        # 设置值
        self.min_y = -self.h - 10  # 最小y坐标
        self.max_y = config.window.height - 1  # 最大y坐标

        self.mode = PlayerMode.SHM  # 设置玩家模式为SHM（静止模式）
        # 初始化索引
        self.loopIter = 0
        self.playerIndex = 0

        # player velocity, max velocity, downward acceleration, acceleration on flap
        self.reset_vals_shm()

    def generate_index(self):
        """生成用于循环显示图像的索引"""
        while True:
            for i in cycle([0, 1, 2, 1]):
                yield i

    def set_mode(self, mode: PlayerMode):
        """设置玩家模式"""
        if mode == self.mode:
            return

        # 记忆原始模式
        self.old_mode = self.mode
        self.mode = mode

        # 根据不同的模式设置不同的值
        if mode == PlayerMode.NORMAL:
            self.reset_vals_normal()
        elif mode == PlayerMode.SHM:
            self.reset_vals_shm()
        elif mode == PlayerMode.REVERSE:
            self.reset_vals_reverse()
        elif mode == PlayerMode.BOSS:
            self.reset_vals_boss()
        elif mode == PlayerMode.CRASH:
            self.reset_vals_crash()

    def reset_vals_normal(self) -> None:
        """设置正常模式下的值"""
        self.vel_y = -9  # 初始速度
        self.max_vel_y = 10  # 最大下降速度
        self.min_vel_y = -8  # 最小上升速度
        self.acc_y = 1  # 重力加速度

        self.rot = 60  # 初始旋转角度
        self.vel_rot = -3  # 旋转速度
        self.rot_min = -90  # 最小旋转角度
        self.rot_max = 20  # 最大旋转角度

        self.flap_acc = -9  # 拍打加速度
        self.flapped = False  # 拍打状态

    def reset_vals_reverse(self) -> None:
        """设置反向模式下的值"""
        self.vel_y = 9  # 初始速度
        self.max_vel_y = 8  # 最大下降速度
        self.min_vel_y = -10  # 最小上升速度
        self.acc_y = -1  # 重力加速度

        self.rot = -60  # 初始旋转角度
        self.vel_rot = 3  # 旋转速度
        self.rot_min = -20  # 最小旋转角度
        self.rot_max = 90  # 最大旋转角度

        self.flap_acc = 9  # 拍打加速度
        self.flapped = False  # 拍打状态
        
    def reset_vals_boss(self) -> None:
        """设置Boss模式下的值"""
        # 与正常模式类似但速度较慢
        self.vel_y = -6  # 初始速度
        self.max_vel_y = 8  # 最大下降速度
        self.min_vel_y = -6  # 最小上升速度
        self.acc_y = 0.8  # 重力加速度

        self.rot = 60  # 初始旋转角度
        self.vel_rot = -2  # 旋转速度
        self.rot_min = -60  # 最小旋转角度
        self.rot_max = 15  # 最大旋转角度

        self.flap_acc = -7  # 拍打加速度
        self.flapped = False  # 拍打状态
        
        # 重置子弹
        self.bullets = []
        self.bullet_cooldown = 0
        self.boss_target = None  # 存储Boss引用，用于追踪弹
        
        # 重置武器弹药
        for weapon in self.weapons:
            if weapon.weapon_type == WeaponType.NORMAL:
                weapon.ammo = -1  # 无限弹药
            elif weapon.weapon_type == WeaponType.TRIPLE:
                weapon.ammo = 30
            elif weapon.weapon_type == WeaponType.LASER:
                weapon.ammo = 100
            elif weapon.weapon_type == WeaponType.HOMING:
                weapon.ammo = 10

    def reset_vals_shm(self) -> None:
        self.vel_y = 1  # player's velocity along Y axis
        self.max_vel_y = 4  # max vel along Y, max descend speed
        self.min_vel_y = -4  # min vel along Y, max ascend speed
        self.acc_y = 0.5  # players downward acceleration

        self.rot = 0  # player's current rotation
        self.vel_rot = 0  # player's rotation speed
        self.rot_min = 0  # player's min rotation angle
        self.rot_max = 0  # player's max rotation angle

        self.flap_acc = 0  # players speed on flapping
        self.flapped = False  # True when player flaps

    def reset_vals_crash(self) -> None:
        self.acc_y = 2
        self.vel_y = 7
        self.max_vel_y = 15
        self.vel_rot = -8

    def update_image(self) -> None:
        """更新玩家的图像"""
        size_scale = getattr(self, 'size_modifier', 1.0)
        if size_scale != 1.0:
            # 应用缩放
            idx = next(self.img_gen)
            original_img = self.config.images.player[idx]
            new_width = int(original_img.get_width() * size_scale)
            new_height = int(original_img.get_height() * size_scale)
            self.image = pygame.transform.scale(original_img, (new_width, new_height))
            self.w = new_width
            self.h = new_height
        else:
            # 正常大小
            self.image = self.config.images.player[next(self.img_gen)]
            self.w = self.image.get_width()
            self.h = self.image.get_height()

    def tick_normal(self) -> None:
        if self.vel_y < self.max_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_modifier
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()

    def tick_reverse(self) -> None:
        """反向模式的更新逻辑"""
        if self.vel_y > self.min_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_modifier
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()
        
    def tick_boss(self) -> None:
        """Boss模式的更新逻辑"""
        # 类似正常模式的移动
        if self.vel_y < self.max_vel_y and not self.flapped:
            self.vel_y += self.acc_y
        if self.flapped:
            self.flapped = False

        # 应用速度修改器
        adjusted_vel_y = self.vel_y * self.speed_modifier
        self.y = clamp(self.y + adjusted_vel_y, self.min_y, self.max_y)
        self.rotate()
        
        # 更新武器冷却时间
        self.update_weapons()
        
        # 更新并绘制子弹
        self.update_bullets()
        
        # 更新爆炸特效
        self.update_explosions()
        
        # 绘制武器UI
        self.draw_weapon_ui()
    
    def update_weapons(self):
        """更新所有武器状态"""
        for weapon in self.weapons:
            weapon.update()
    
    def update_bullets(self):
        """更新并绘制所有子弹"""
        for bullet in list(self.bullets):
            if hasattr(bullet, 'is_homing') and bullet.is_homing:
                # 更新追踪弹的目标
                bullet.target = self.boss_target
                
            bullet.tick()
            # 移除超出屏幕的子弹
            if bullet.is_out_of_screen():
                self.bullets.remove(bullet)
    
    def draw_weapon_ui(self):
        """绘制当前武器信息UI"""
        weapon = self.weapons[self.current_weapon_index]
        
        # 创建武器信息背景 - 更好的设计
        bg_width = 115
        bg_height = 45
        bg = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        
        # 添加圆角边框效果 - 减小边框宽度
        pygame.draw.rect(bg, (255, 255, 255, 70), pygame.Rect(0, 0, bg_width, bg_height), 1, border_radius=3)
        
        self.config.screen.blit(bg, self.bullet_ui_pos)
        
        # 使用中文字体 - 减小字体
        font = get_font('SimHei', 12)
        small_font = get_font('SimHei', 9)
        
        # 绘制武器图标 - 略微调整位置
        icon_size = 18
        icon_x = self.bullet_ui_pos[0] + 10
        icon_y = self.bullet_ui_pos[1] + 10
        
        # 圆形图标背景
        icon_bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        pygame.draw.circle(icon_bg, weapon.color, (icon_size//2, icon_size//2), icon_size//2)
        
        # 根据武器类型绘制不同图标
        if weapon.weapon_type == WeaponType.NORMAL:
            # 普通子弹图标 - 圆形
            pygame.draw.circle(icon_bg, (255, 255, 255), (icon_size//2, icon_size//2), icon_size//4)
        elif weapon.weapon_type == WeaponType.TRIPLE:
            # 三连发图标 - 三个点
            for i in range(3):
                x = icon_size//2
                y = 4 + i * 5
                pygame.draw.circle(icon_bg, (255, 255, 255), (x, y), 1)
        elif weapon.weapon_type == WeaponType.LASER:
            # 激光图标 - 线
            pygame.draw.line(icon_bg, (255, 255, 255), (4, icon_size//2), (icon_size-4, icon_size//2), 2)
        elif weapon.weapon_type == WeaponType.HOMING:
            # 追踪图标 - 箭头
            pygame.draw.polygon(icon_bg, (255, 255, 255), 
                              [(4, 4), (icon_size-4, icon_size//2), (4, icon_size-4)])
        
        self.config.screen.blit(icon_bg, (icon_x, icon_y))
        
        # 简化武器名称 - 移除"子弹"等
        name_map = {
            "基础子弹": "基础",
            "三连发": "三连",
            "激光": "激光",
            "追踪导弹": "追踪"
        }
        short_name = name_map.get(weapon.weapon_type.value, weapon.weapon_type.value)
        
        # 显示武器名称 - 在图标旁边
        name_text = font.render(short_name, True, weapon.color)
        self.config.screen.blit(name_text, (icon_x + icon_size + 5, icon_y))
        
        # 弹药符号
        ammo_text = "∞" if weapon.ammo < 0 else f"{weapon.ammo}"
        ammo_surface = font.render(f"{ammo_text}", True, (255, 255, 255))
        self.config.screen.blit(ammo_surface, (icon_x + icon_size + 5, icon_y + 20))
        
        # 快捷键提示 - 在底部，更短
        keys_text = small_font.render("Q/E切换", True, (180, 180, 180))
        self.config.screen.blit(keys_text, (self.bullet_ui_pos[0] + bg_width//2 - keys_text.get_width()//2, 
                                            self.bullet_ui_pos[1] + bg_height - 12))

    def update_explosions(self):
        """更新爆炸特效"""
        explosions_to_remove = []
        
        for explosion in self.explosions:
            # 更新位置
            explosion['x'] += explosion['vel_x']
            explosion['y'] += explosion['vel_y']
            
            # 减少持续时间
            explosion['duration'] -= 1
            
            # 绘制粒子
            if explosion['duration'] > 0:
                pygame.draw.circle(
                    self.config.screen,
                    explosion['color'],
                    (int(explosion['x']), int(explosion['y'])),
                    int(explosion['size'] * (explosion['duration'] / 20))
                )
            else:
                explosions_to_remove.append(explosion)
        
        # 移除已完成的爆炸
        for explosion in explosions_to_remove:
            if explosion in self.explosions:
                self.explosions.remove(explosion)

    def tick_shm(self) -> None:
        """有规律地上下移动玩家，用于显示欢迎界面"""
        self.loopIter = (self.loopIter + 1) % 28
        if self.loopIter == 0:
            self.playerIndex = next(self.img_gen)
            self.image = self.config.images.player[self.playerIndex]

        if self.loopIter % 14 == 0:
            self.vel_y = -self.vel_y

        self.y += self.vel_y

    def tick_crash(self) -> None:
        if self.min_y <= self.y <= self.max_y:
            self.y = clamp(self.y + self.vel_y, self.min_y, self.max_y)
            # rotate only when it's a pipe crash and bird is still falling
            if self.crash_entity != "floor":
                self.rotate()

        # player velocity change
        if self.vel_y < 15:
            self.vel_y += self.acc_y

    def rotate(self) -> None:
        self.rot = clamp(self.rot + self.vel_rot, self.rot_min, self.rot_max)

    def draw(self) -> None:
        self.update_image()
        if self.mode == PlayerMode.SHM:
            self.tick_shm()
        elif self.mode == PlayerMode.NORMAL:
            self.tick_normal()
        elif self.mode == PlayerMode.REVERSE:
            self.tick_reverse()
        elif self.mode == PlayerMode.BOSS:
            self.tick_boss()
        elif self.mode == PlayerMode.CRASH:
            self.tick_crash()
        
        self.draw_player()

    def draw_player(self) -> None:
        # Rotate bird for normal mode bird and crashed bird (in air)
        if (
            self.mode == PlayerMode.NORMAL
            or self.mode == PlayerMode.REVERSE
            or self.mode == PlayerMode.BOSS
            or (self.mode == PlayerMode.CRASH and self.y < self.max_y - 30)
        ):
            rotation = self.rot if self.mode != PlayerMode.REVERSE else -self.rot
            # pygame.transform.rotate rotates clockwise (opposite of what we want)
            img = pygame.transform.rotate(self.image, rotation)
            rotated_rect = img.get_rect(center=(self.x + self.w // 2, self.y + self.h // 2))
            
            # 如果处于无敌状态，添加视觉特效
            if self.invincible:
                # 创建闪光效果
                shine_tick = pygame.time.get_ticks() / 100  # 使闪光效果随时间变化
                shine_alpha = int(128 + 127 * math.sin(shine_tick))  # 在128-255之间变化
                
                # 创建一个稍大的金色光环
                glow_size = max(img.get_width(), img.get_height()) + 12
                glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                
                # 绘制金色光环
                for i in range(3):
                    glow_radius = glow_size // 2 - i * 2
                    # 金色的RGB值，透明度随时间变化
                    gold_color = (255, 215, 0, max(40, shine_alpha - i * 30))
                    pygame.draw.circle(
                        glow_surface,
                        gold_color,
                        (glow_size // 2, glow_size // 2),
                        glow_radius
                    )
                
                # 在玩家周围绘制金色保护罩
                shield_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                shield_alpha = min(180, shine_alpha)
                pygame.draw.circle(
                    shield_surface,
                    (255, 215, 0, shield_alpha // 3),  # 金色半透明
                    (glow_size // 2, glow_size // 2),
                    glow_size // 2 - 2,
                    3  # 边框宽度
                )
                
                # 闪烁星星效果
                star_tick = pygame.time.get_ticks() / 200
                for i in range(4):
                    star_angle = star_tick + i * (math.pi / 2)
                    star_dist = glow_size // 3
                    star_x = glow_size//2 + star_dist * math.cos(star_angle)
                    star_y = glow_size//2 + star_dist * math.sin(star_angle)
                    star_size = 2 + math.sin(star_tick * 2 + i) * 1.5
                    
                    # 绘制星星
                    pygame.draw.circle(
                        shield_surface,
                        (255, 255, 255, shield_alpha),
                        (int(star_x), int(star_y)),
                        star_size
                    )
                
                # 将光环和护盾绘制到屏幕上，确保玩家图像居中
                glow_rect = glow_surface.get_rect(center=rotated_rect.center)
                self.config.screen.blit(glow_surface, glow_rect)
                self.config.screen.blit(shield_surface, glow_rect)
            
            self.config.screen.blit(img, rotated_rect)
        # For crashed bird on ground or message bird
        else:
            self.config.screen.blit(self.image, (self.x, self.y))
    
    def switch_weapon(self, direction: int) -> None:
        """切换武器 (1: 下一个, -1: 上一个)"""
        self.current_weapon_index = (self.current_weapon_index + direction) % len(self.weapons)
        
        # 更新子弹伤害值
        self.bullet_damage = self.weapons[self.current_weapon_index].damage
        
        # 播放切换音效
        self.config.sounds.swoosh.play()

    def shoot(self) -> None:
        """玩家发射子弹"""
        weapon = self.weapons[self.current_weapon_index]
        
        if not weapon.can_fire():
            return
            
        # 使用当前武器开火
        new_bullets = weapon.fire(
            self.x + self.w,
            self.y + self.h // 2 - 4,
            target=self.boss_target  # 用于追踪弹
        )
        
        # 添加到子弹列表
        self.bullets.extend(new_bullets)

    def stop_wings(self) -> None:
        self.img_gen = cycle([0])

    def flap(self) -> None:
        if self.mode != PlayerMode.CRASH:
            if self.mode == PlayerMode.REVERSE:
                # 反向模式下的拍打
                self.vel_y = self.flap_acc
            else:
                # 正常模式或Boss模式下的拍打
                self.vel_y = self.flap_acc
            
            self.flapped = True
            # 重置旋转值
            if self.mode == PlayerMode.NORMAL or self.mode == PlayerMode.BOSS:
                self.rot = 80
            elif self.mode == PlayerMode.REVERSE:
                self.rot = -80

    def crossed(self, pipe: Pipe) -> bool:
        return pipe.x < self.x < pipe.x + pipe.w

    def collided(self, pipes: Pipes, floor: Floor) -> bool:
        """检查是否与管道或地板发生碰撞"""
        # 如果处于无敌状态，直接返回False（不会碰撞）
        if hasattr(self, 'invincible') and self.invincible:
            return False
            
        if (
            self.y + self.h >= floor.y - 1  # bird on floor
            or self.y < 0  # bird above viewport
        ):
            self.crash_entity = "floor"
            return True

        for pipe in pipes.upper + pipes.lower:
            if self.collide(pipe):
                self.crash_entity = "pipe"
                return True

        return False
        
    def check_boss_bullet_collision(self, boss) -> bool:
        """检查玩家是否被Boss子弹击中"""
        for bullet in boss.bullets:
            if self.collide(bullet):
                # 只有非无敌状态下才会受到伤害
                if not self.invincible:
                    # 创建爆炸效果
                    self.create_explosion(self.x + self.w//2, self.y + self.h//2, (255, 100, 100))
                    
                    # 播放碰撞音效
                    self.config.sounds.die.play()
                    
                    # 从Boss的子弹列表中移除
                    boss.bullets.remove(bullet)
                    
                    return True
                else:
                    # 无敌状态下子弹被弹开但不造成伤害
                    boss.bullets.remove(bullet)
                    
                    # 播放无敌反弹音效
                    self.config.sounds.swoosh.play()
                    
                    # 创建反弹效果
                    self.create_explosion(self.x + self.w//2, self.y + self.h//2, (255, 215, 0))
        
        return False
    
    def check_bullet_hit_boss(self, boss) -> bool:
        """检查玩家的子弹是否击中Boss"""
        hit = False
        for bullet in list(self.bullets):
            # 判断玩家子弹与Boss的碰撞
            if bullet.collide(boss):
                # 应用伤害
                boss.take_damage(bullet.damage)
                # 移除子弹
                self.bullets.remove(bullet)
                hit = True
        
        return hit

    def create_explosion(self, x, y, color):
        """创建爆炸特效"""
        # 爆炸特效参数
        particles = 12
        size = 3
        speed = 2
        duration = 20
        
        for i in range(particles):
            angle = random.random() * math.pi * 2
            vel_x = math.cos(angle) * speed * random.random()
            vel_y = math.sin(angle) * speed * random.random()
            
            self.explosions.append({
                'x': x,
                'y': y,
                'vel_x': vel_x,
                'vel_y': vel_y,
                'size': size,
                'color': color,
                'duration': duration
            })
