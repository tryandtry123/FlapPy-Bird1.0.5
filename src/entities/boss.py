import random
import pygame
import math
from typing import List
from enum import Enum

from ..utils import GameConfig
from .entity import Entity
from .bullet import Bullet


class BossType(Enum):
    """Boss类型枚举"""
    NORMAL = "普通Boss"    # 基础红色Boss
    SPEEDY = "速度型Boss"   # 蓝色高速Boss
    SPLITTER = "分裂型Boss" # 绿色分裂Boss
    TANK = "坦克型Boss"     # 紫色高防Boss


# 新增伤害数字显示类
class DamageText:
    """显示伤害数值的飘动文本"""
    def __init__(self, config, x, y, damage, color=(255, 255, 255)):
        self.config = config
        self.x = x
        self.y = y
        self.damage = damage
        self.color = color
        self.life = 30  # 显示帧数
        self.velocity_y = -1.5  # 向上飘动速度
        self.alpha = 255  # 透明度
        
        # 创建字体
        try:
            self.font = pygame.font.SysFont('Arial', 14)
        except:
            self.font = pygame.font.Font(None, 14)
    
    def tick(self):
        """更新伤害文本状态"""
        self.life -= 1
        self.y += self.velocity_y
        
        # 逐渐降低透明度
        if self.life < 10:
            self.alpha = int(self.alpha * 0.8)
        
        # 渲染文本
        text = self.font.render(f"{self.damage}", True, self.color)
        text_surface = pygame.Surface(text.get_size(), pygame.SRCALPHA)
        text_surface.fill((0, 0, 0, 0))  # 透明背景
        text_surface.blit(text, (0, 0))
        
        # 应用透明度
        text_surface.set_alpha(self.alpha)
        
        # 绘制到屏幕上
        self.config.screen.blit(text_surface, (self.x, self.y))
        
        return self.life > 0  # 返回是否仍然存活


class Boss(Entity):
    """Boss实体类"""
    
    def __init__(self, config: GameConfig, boss_type: BossType = BossType.NORMAL) -> None:
        # 设置Boss类型
        self.boss_type = boss_type
        
        # 添加准备阶段属性
        self.preparation_time = 60  # 准备时间（帧数）：约2秒
        self.is_preparing = True    # 是否处于准备阶段
        
        # 新增伤害文本列表
        self.damage_texts = []
        
        # 根据Boss类型设置属性
        if boss_type == BossType.NORMAL:
            self.base_size = 100
            self.y_offset = 0
            self.health = 100  
            self.max_health = 100
            self.speed = 2     
            self.direction = 1 
            self.bullet_cooldown = 0  
            self.bullet_rate = 60     
            self.hit_flash = 0    
            self.default_color = (255, 0, 0)  # 红色Boss
            
        elif boss_type == BossType.SPEEDY:
            self.base_size = 80   # 略小一些
            self.y_offset = 0
            self.health = 80      # 血量少一些
            self.max_health = 80
            self.speed = 4        # 更快的移动速度
            self.direction = 1  
            self.bullet_cooldown = 0  
            self.bullet_rate = 30  # 更快的射击频率
            self.hit_flash = 0   
            self.default_color = (0, 0, 255)  # 蓝色Boss
            
        elif boss_type == BossType.SPLITTER:
            self.base_size = 120  # 更大一些
            self.y_offset = 0
            self.health = 120     # 血量多一些
            self.max_health = 120
            self.speed = 1.5      # 较慢
            self.direction = 1  
            self.bullet_cooldown = 0  
            self.bullet_rate = 90  # 较慢的射击频率
            self.hit_flash = 0   
            self.default_color = (0, 255, 0)  # 绿色Boss
            self.split_threshold = 40  # 血量低于此值时分裂
            self.has_split = False     # 是否已分裂
            
        elif boss_type == BossType.TANK:
            self.base_size = 140  # 非常大
            self.y_offset = 0
            self.health = 200     # 血量非常多
            self.max_health = 200
            self.speed = 1        # 非常慢
            self.direction = 1  
            self.bullet_cooldown = 0  
            self.bullet_rate = 120 # 很慢的射击频率
            self.hit_flash = 0   
            self.default_color = (128, 0, 128)  # 紫色Boss
        
        self.bullets: List[Bullet] = []  # Boss发射的子弹
        
        # 创建Boss图像
        surface = self.create_boss_appearance()
        
        # 设置位置 (右侧屏幕)
        x = config.window.width - self.base_size - 40
        y = config.window.height // 2 - self.base_size // 2
        
        super().__init__(config, surface, x, y)
        
        # 动画属性
        self.animation_tick = 0
        
        # 为Boss添加循环级别属性
        self.level = 1  # 默认级别为1
        
    def create_boss_appearance(self):
        """根据Boss类型创建外观"""
        surface = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
        
        # 绘制Boss主体
        pygame.draw.circle(surface, self.default_color, (self.base_size//2, self.base_size//2), self.base_size//2)
        
        # 根据类型添加特殊外观
        if self.boss_type == BossType.NORMAL:
            # 普通Boss - 基本的眼睛和嘴巴
            self.draw_basic_face(surface)
            
        elif self.boss_type == BossType.SPEEDY:
            # 速度型Boss - 添加速度线条和尖锐眼睛
            self.draw_basic_face(surface)
            self.draw_speed_lines(surface)
            
        elif self.boss_type == BossType.SPLITTER:
            # 分裂型Boss - 添加分裂纹理
            self.draw_basic_face(surface)
            self.draw_split_pattern(surface)
            
        elif self.boss_type == BossType.TANK:
            # 坦克型Boss - 添加装甲纹理
            self.draw_basic_face(surface)
            self.draw_armor_pattern(surface)
        
        return surface
    
    def draw_basic_face(self, surface):
        """绘制基本的脸部特征"""
        # 添加眼睛
        eye_size = self.base_size // 6
        eye_offset = self.base_size // 4
        pygame.draw.circle(surface, (255, 255, 255), 
                          (self.base_size//2 - eye_offset, self.base_size//2 - eye_offset), 
                          eye_size)
        pygame.draw.circle(surface, (255, 255, 255), 
                          (self.base_size//2 + eye_offset, self.base_size//2 - eye_offset), 
                          eye_size)
        
        # 添加眼球
        pupil_size = eye_size // 2
        pygame.draw.circle(surface, (0, 0, 0), 
                          (self.base_size//2 - eye_offset, self.base_size//2 - eye_offset), 
                          pupil_size)
        pygame.draw.circle(surface, (0, 0, 0), 
                          (self.base_size//2 + eye_offset, self.base_size//2 - eye_offset), 
                          pupil_size)
        
        # 添加嘴巴
        mouth_width = self.base_size // 2
        mouth_height = self.base_size // 8
        mouth_rect = pygame.Rect(
            self.base_size//2 - mouth_width//2,
            self.base_size//2 + eye_offset,
            mouth_width,
            mouth_height
        )
        pygame.draw.rect(surface, (0, 0, 0), mouth_rect)
    
    def draw_speed_lines(self, surface):
        """为速度型Boss添加速度线条"""
        for i in range(5):
            start_x = self.base_size // 10
            end_x = self.base_size // 3
            y = self.base_size // 3 + i * (self.base_size // 10)
            
            pygame.draw.line(surface, (200, 200, 255), 
                            (start_x, y), (end_x, y), 2)
    
    def draw_split_pattern(self, surface):
        """为分裂型Boss添加分裂纹理"""
        center_x = self.base_size // 2
        center_y = self.base_size // 2
        
        # 绘制分裂线
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = center_x + int(0.3 * self.base_size * math.cos(rad))
            y1 = center_y + int(0.3 * self.base_size * math.sin(rad))
            x2 = center_x + int(0.5 * self.base_size * math.cos(rad))
            y2 = center_y + int(0.5 * self.base_size * math.sin(rad))
            
            pygame.draw.line(surface, (0, 200, 0), (x1, y1), (x2, y2), 3)
    
    def draw_armor_pattern(self, surface):
        """为坦克型Boss添加装甲纹理"""
        # 绘制装甲板
        armor_rects = [
            (self.base_size//4, self.base_size//8, self.base_size//2, self.base_size//10),
            (self.base_size//8, self.base_size//3, self.base_size//10, self.base_size//3),
            (self.base_size - self.base_size//8 - self.base_size//10, self.base_size//3, self.base_size//10, self.base_size//3),
            (self.base_size//4, self.base_size - self.base_size//8 - self.base_size//10, self.base_size//2, self.base_size//10)
        ]
        
        for rect in armor_rects:
            pygame.draw.rect(surface, (180, 180, 180), rect)
            pygame.draw.rect(surface, (100, 100, 100), rect, 2)
    
    def tick(self) -> None:
        """更新Boss状态"""
        self.move()
        
        # 更新准备阶段
        if self.is_preparing:
            self.preparation_time -= 1
            if self.preparation_time <= 0:
                self.is_preparing = False
                # 播放准备完成音效
                self.config.sounds.swoosh.play()
            # 准备阶段不攻击
            self.update_bullets()
            self.animation_tick += 1
            self.special_behavior()
            
            # 更新并绘制伤害文本
            self.update_damage_texts()
            
            self.draw()
            return
            
        # 管理射击冷却
        if self.bullet_cooldown > 0:
            self.bullet_cooldown -= 1
        
        # 检查是否可以射击
        if self.bullet_cooldown <= 0:
            self.shoot()
            self.bullet_cooldown = self.bullet_rate
        
        # 更新动画
        self.animation_tick += 1
        
        # 更新并绘制子弹
        self.update_bullets()
        
        # 更新并绘制伤害文本
        self.update_damage_texts()
        
        # 特殊行为
        self.special_behavior()
        
        # 绘制Boss
        self.draw()
    
    def draw(self) -> None:
        # 受击闪烁效果
        if self.hit_flash > 0:
            self.hit_flash -= 1
            flash_color = (255, 255, 255)
            surface = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
            pygame.draw.circle(surface, flash_color, (self.base_size//2, self.base_size//2), self.base_size//2)
            self.config.screen.blit(surface, (self.x, self.y))
        else:
            # 确保恢复正常显示
            if not hasattr(self, 'normal_displayed') or not self.normal_displayed:
                self.image = self.create_boss_appearance()
                self.normal_displayed = True
            # 正常绘制
            self.config.screen.blit(self.image, (self.x, self.y))
            
        # 直接在Boss头上方绘制血条
        self.draw_health_bar_overhead()
        
        # 准备阶段显示提示和准备进度条
        if self.is_preparing:
            try:
                warning_font = pygame.font.SysFont('Arial', 18)
            except:
                warning_font = pygame.font.Font(None, 18)
                
            warning_text = warning_font.render("准备攻击...", True, (255, 50, 50))
            text_x = self.x + (self.base_size - warning_text.get_width()) // 2
            text_y = self.y - 30
            self.config.screen.blit(warning_text, (text_x, text_y))
            
            # 添加准备进度条
            # 获取初始准备时间
            if not hasattr(self, 'initial_preparation_time'):
                self.initial_preparation_time = 60  # 默认值
                if hasattr(self, 'preparation_time'):
                    # 在第一次调用时设置初始准备时间
                    self.initial_preparation_time = self.preparation_time
            
            # 计算进度
            progress = 1.0
            if self.initial_preparation_time > 0:
                progress = max(0, min(1, self.preparation_time / self.initial_preparation_time))
            
            # 绘制进度条背景
            bar_width = self.base_size * 0.8
            bar_height = 6
            bar_x = self.x + (self.base_size - bar_width) // 2
            bar_y = self.y - 40
            
            # 背景
            pygame.draw.rect(self.config.screen, (50, 50, 50, 180), 
                            pygame.Rect(bar_x, bar_y, bar_width, bar_height))
            
            # 进度
            progress_width = bar_width * progress
            if progress > 0:
                # 修改颜色渐变逻辑，使用更平滑的黄色到绿色过渡，去除红色
                if progress > 0.5:
                    # 从黄色到绿色
                    green = 255
                    red = int(255 * 2 * (1 - progress))
                    bar_color = (red, green, 0)
                else:
                    # 从橙色到黄色
                    red = 255
                    green = int(255 * progress * 2)
                    bar_color = (red, green, 0)
                
                pygame.draw.rect(self.config.screen, bar_color, 
                                pygame.Rect(bar_x, bar_y, progress_width, bar_height))
            
            # 边框 - 使用白色半透明边框
            pygame.draw.rect(self.config.screen, (255, 255, 255, 100), 
                            pygame.Rect(bar_x, bar_y, bar_width, bar_height), 1)
    
    def draw_health_bar_overhead(self) -> None:
        """直接在Boss头上方绘制生命条"""
        # 血条宽度为Boss直径的80%
        bar_width = int(self.base_size * 0.8)
        bar_height = 6
        
        # 位置：居中在Boss顶部上方
        bar_x = self.x + (self.base_size - bar_width) // 2
        bar_y = self.y - bar_height - 5  # 在Boss上方5像素
        
        # 确保血条不会超出屏幕顶部
        if bar_y < 0:
            bar_y = 0
        
        # 绘制背景
        bg_color = (0, 0, 0, 180)  # 半透明黑色
        bg_surface = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        bg_surface.fill(bg_color)
        self.config.screen.blit(bg_surface, (bar_x, bar_y))
        
        # 计算血条长度
        health_percent = self.health / self.max_health
        health_width = int(bar_width * health_percent)
        
        # 根据血量选择颜色
        if health_percent > 0.7:
            health_color = (0, 255, 0)  # 绿色
        elif health_percent > 0.3:
            health_color = (255, 255, 0)  # 黄色
        else:
            health_color = (255, 0, 0)  # 红色
        
        # 绘制血条
        if health_width > 0:  # 确保血量大于0才绘制
            health_surface = pygame.Surface((health_width, bar_height), pygame.SRCALPHA)
            health_surface.fill(health_color)
            self.config.screen.blit(health_surface, (bar_x, bar_y))
        
        # 添加边框
        pygame.draw.rect(self.config.screen, (255, 255, 255, 100), 
                         pygame.Rect(bar_x, bar_y, bar_width, bar_height), 1)
        
        # 添加血量数值显示
        try:
            hp_font = pygame.font.SysFont('Arial', 10)
        except:
            hp_font = pygame.font.Font(None, 10)
        
        hp_text = hp_font.render(f"{int(self.health)}/{self.max_health}", True, (255, 255, 255))
        hp_text_rect = hp_text.get_rect(midleft=(bar_x + bar_width + 5, bar_y + bar_height // 2))
        self.config.screen.blit(hp_text, hp_text_rect)
        
        # 如果是Boss战斗的第二轮或以上，在血条旁显示等级
        if hasattr(self, 'level') and self.level > 1:
            # 使用小字体
            try:
                level_font = pygame.font.SysFont('Arial', 12)
            except:
                level_font = pygame.font.Font(None, 12)
            
            level_text = level_font.render(f"Lv{self.level}", True, (255, 255, 255))
            self.config.screen.blit(level_text, (bar_x + bar_width + 2, bar_y))
    
    def special_behavior(self):
        """根据Boss类型执行特殊行为"""
        # 分裂型Boss特殊行为
        if self.boss_type == BossType.SPLITTER and self.health <= self.split_threshold and not self.has_split:
            self.has_split = True
            self.split()
            
    def split(self):
        """分裂型Boss分裂行为"""
        # 当生命值低于阈值时，分裂出两个小Boss
        for i in range(2):
            # 创建子弹代表分裂物
            offset_y = 50 if i == 0 else -50
            bullet = Bullet(self.config, self.x, self.y + offset_y)
            
            # 设置子弹属性
            bullet.vel_x = -3
            bullet.vel_y = 1 if i == 0 else -1
            bullet.damage = 1
            
            # 设置外观 - 小一点的绿色圆形
            size = 20
            bullet_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(bullet_surface, self.default_color, (size//2, size//2), size//2)
            bullet.image = bullet_surface
            
            # 添加到子弹列表
            self.bullets.append(bullet)
            
        # 播放分裂音效
        self.config.sounds.hit.play()
        
    def move(self) -> None:
        """移动Boss"""
        # 简单的上下移动
        self.animation_tick += 1
        
        # 更改方向
        if self.y <= 50:
            self.direction = 1
        elif self.y >= self.config.window.viewport_height - self.h - 50:
            self.direction = -1
            
        # 根据Boss类型设置移动行为
        if self.boss_type == BossType.NORMAL:
            # 普通Boss - 正常移动
            if self.animation_tick % 120 == 0 and random.random() < 0.3:
                self.direction *= -1
                
        elif self.boss_type == BossType.SPEEDY:
            # 速度型Boss - 更频繁地改变方向
            if self.animation_tick % 60 == 0 and random.random() < 0.5:
                self.direction *= -1
                
        elif self.boss_type == BossType.SPLITTER:
            # 分裂型Boss - 在生命值低时更慢
            if self.health < self.split_threshold:
                actual_speed = self.speed * 0.5
            else:
                actual_speed = self.speed
                
            self.y += actual_speed * self.direction
            return
            
        elif self.boss_type == BossType.TANK:
            # 坦克型Boss - 偶尔停顿
            if self.animation_tick % 180 < 60:  # 每180帧停顿60帧
                return  # 不移动
            
        # 应用移动
        self.y += self.speed * self.direction
    
    def shoot(self) -> None:
        """Boss发射子弹"""
        # 根据Boss类型选择攻击模式
        if self.boss_type == BossType.NORMAL:
            self.normal_shoot()
            
        elif self.boss_type == BossType.SPEEDY:
            self.speedy_shoot()
            
        elif self.boss_type == BossType.SPLITTER:
            self.splitter_shoot()
            
        elif self.boss_type == BossType.TANK:
            self.tank_shoot()
    
    def normal_shoot(self) -> None:
        """普通Boss直线射击"""
        # 创建子弹
        bullet_surface = pygame.Surface((15, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(bullet_surface, (255, 0, 0), bullet_surface.get_rect())
        
        # 从嘴巴位置发射
        bullet_x = self.x - 10
        bullet_y = self.y + self.h // 2
        
        bullet = Bullet(self.config, bullet_x, bullet_y)
        bullet.image = bullet_surface
        bullet.vel_x = -8  # 向左飞行
        bullet.damage = 1
        
        self.bullets.append(bullet)
        
        # 播放声音效果
        self.config.sounds.swoosh.play()
    
    def speedy_shoot(self) -> None:
        """速度型Boss三连射"""
        for i in range(3):
            bullet_surface = pygame.Surface((10, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(bullet_surface, (0, 0, 255), bullet_surface.get_rect())
            
            # 从嘴巴位置发射
            bullet_x = self.x - 10
            bullet_y = self.y + self.h // 2
            
            bullet = Bullet(self.config, bullet_x, bullet_y)
            bullet.image = bullet_surface
            bullet.vel_x = -12  # 更快速度
            bullet.delay = i * 5  # 设置发射延迟
            bullet.damage = 1
            
            self.bullets.append(bullet)
        
        # 播放声音效果
        self.config.sounds.swoosh.play()
    
    def splitter_shoot(self) -> None:
        """分裂型Boss发射分裂子弹"""
        bullet_surface = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(bullet_surface, (0, 255, 0), (6, 6), 6)
        
        # 从嘴巴位置发射
        bullet_x = self.x - 10
        bullet_y = self.y + self.h // 2
        
        bullet = Bullet(self.config, bullet_x, bullet_y)
        bullet.image = bullet_surface
        bullet.vel_x = -6  # 慢一些
        bullet.is_splitter = True
        bullet.split_time = 30  # 30帧后分裂
        bullet.damage = 1
        bullet.parent = self  # 添加父对象引用
        
        self.bullets.append(bullet)
        
        # 播放声音效果
        self.config.sounds.swoosh.play()
    
    def tank_shoot(self) -> None:
        """坦克型Boss发射大型子弹"""
        bullet_surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(bullet_surface, (128, 0, 128), (10, 10), 10)
        
        # 从嘴巴位置发射
        bullet_x = self.x - 20
        bullet_y = self.y + self.h // 2
        
        bullet = Bullet(self.config, bullet_x, bullet_y)
        bullet.image = bullet_surface
        bullet.vel_x = -5  # 慢一些
        bullet.damage = 2  # 伤害更高
        
        self.bullets.append(bullet)
        
        # 播放声音效果
        self.config.sounds.swoosh.play()
        
    def take_damage(self, damage: int) -> None:
        """Boss受到伤害"""
        self.health -= damage
        self.hit_flash = 5  # 设置闪烁帧数
        
        # 播放受击声音
        self.config.sounds.hit.play()
        
        # 坦克Boss在低血量时受到的伤害减半
        if self.boss_type == BossType.TANK and self.health < self.max_health * 0.5:
            self.health += damage // 2  # 恢复一半伤害
        
        # 确保生命值不为负
        if self.health < 0:
            self.health = 0
            
        # 创建伤害数值显示
        # 在Boss身体上随机位置显示，增加一些随机性
        x_offset = random.randint(-int(self.base_size * 0.3), int(self.base_size * 0.3))
        y_offset = random.randint(-int(self.base_size * 0.3), int(self.base_size * 0.3))
        
        # 根据伤害值选择颜色
        if damage >= 5:
            color = (255, 50, 50)  # 大伤害红色
        elif damage >= 3:
            color = (255, 255, 0)  # 中等伤害黄色
        else:
            color = (255, 255, 255)  # 普通伤害白色
            
        # 添加到伤害文本列表
        damage_text = DamageText(
            self.config, 
            self.x + self.base_size // 2 + x_offset, 
            self.y + self.base_size // 2 + y_offset,
            damage,
            color
        )
        self.damage_texts.append(damage_text)
    
    def is_defeated(self) -> bool:
        """检查Boss是否被击败"""
        # 不再输出调试信息
        if self.health <= 0:
            return True
        return False
    
    def draw_health_bar(self) -> None:
        """绘制Boss生命条"""
        bar_width = 200
        bar_height = 20
        x = self.config.window.width - bar_width - 20
        y = 20
        
        # 绘制底部背景
        pygame.draw.rect(self.config.screen, (50, 50, 50), 
                        (x, y, bar_width, bar_height))
        
        # 计算当前生命值对应的宽度
        health_width = int((self.health / self.max_health) * bar_width)
        
        # 根据生命值选择颜色
        if self.health > self.max_health * 0.6:
            color = (0, 255, 0)  # 绿色
        elif self.health > self.max_health * 0.3:
            color = (255, 255, 0)  # 黄色
        else:
            color = (255, 0, 0)  # 红色
            
        # 绘制生命值
        pygame.draw.rect(self.config.screen, color, 
                        (x, y, health_width, bar_height))
        
        # 绘制边框
        pygame.draw.rect(self.config.screen, (200, 200, 200), 
                        (x, y, bar_width, bar_height), 2)
        
        # 添加文字和Boss类型 - 使用默认字体避免乱码
        try:
            # 尝试使用Arial字体 - 几乎所有Windows系统都有
            font = pygame.font.SysFont('Arial', 16)
            # 显示简化的文本
            text = font.render(f"HP: {self.health}/{self.max_health}", True, (255, 255, 255))
        except:
            # 如果失败，使用系统默认字体
            font = pygame.font.Font(None, 16)
            text = font.render(f"HP: {self.health}/{self.max_health}", True, (255, 255, 255))
            
        text_rect = text.get_rect(center=(x + bar_width // 2, y + bar_height // 2))
        self.config.screen.blit(text, text_rect)
    
    def update_bullets(self):
        """更新并绘制Boss的子弹"""
        for bullet in list(self.bullets):
            bullet.tick()
            # 移除超出屏幕的子弹
            if bullet.is_out_of_screen():
                self.bullets.remove(bullet) 
    
    def update_damage_texts(self):
        """更新并绘制伤害文本"""
        # 保存仍然存活的伤害文本
        active_texts = []
        
        # 更新并绘制每个伤害文本
        for damage_text in self.damage_texts:
            if damage_text.tick():  # 如果文本仍然存活
                active_texts.append(damage_text)
        
        # 更新伤害文本列表
        self.damage_texts = active_texts 