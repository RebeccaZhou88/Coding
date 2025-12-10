import pygame
import random
import sys
import os
from datetime import datetime
 
# 初始化pygame和混音器
pygame.init() 
pygame.mixer.init() 
 
# 设置随机种子（基于今日日期）
random.seed(datetime.now().timestamp()) 
 
# 获取资源文件夹路径（支持exe打包）
if getattr(sys, 'frozen', False):
    # exe环境
    base_path = sys._MEIPASS
else:
    # 开发环境
    base_path = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(filename):
    return os.path.join(base_path, filename)

# 游戏窗口 
WIDTH, HEIGHT = 700, 800
screen = pygame.display.set_mode((WIDTH,  HEIGHT))
pygame.display.set_caption(" 打飞机 - 2025.12.10")
 
# 颜色定义 
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
 
# 加载资源 (素材文件与AirplaneGame.py同目录)
player_img = pygame.image.load(get_asset_path("player.png")).convert_alpha() 
enemy_img = pygame.image.load(get_asset_path("enemy.png")).convert_alpha() 
bullet_img = pygame.image.load(get_asset_path("bullet.png")).convert_alpha() 
bg_music = pygame.mixer.Sound(get_asset_path("bg_music.mp3")) 
explosion_sound = pygame.mixer.Sound(get_asset_path("explose.wav")) 
hit_sound = pygame.mixer.Sound(get_asset_path("hit.wav")) 
 
# 玩家类
class Player(pygame.sprite.Sprite): 
    def __init__(self):
        super().__init__()
        self.image  = player_img
        self.rect  = self.image.get_rect(center=(WIDTH//2,  HEIGHT-100))
        self.speed  = 8
 
    def update(self):
        keys = pygame.key.get_pressed() 
        if keys[pygame.K_LEFT] and self.rect.left  > 0:
            self.rect.x  -= self.speed 
        if keys[pygame.K_RIGHT] and self.rect.right  < WIDTH:
            self.rect.x  += self.speed 
 
    def shoot(self):
        return Bullet(self.rect.centerx,  self.rect.top) 
 
# 敌机类
class Enemy(pygame.sprite.Sprite): 
    def __init__(self):
        super().__init__()
        self.image  = enemy_img
        self.rect  = self.image.get_rect(center=(random.randint(30,  WIDTH-30), -30))
        self.speed  = random.randint(5,  10)
 
    def update(self):
        self.rect.y  += self.speed 
        if self.rect.top  > HEIGHT:
            self.kill() 
 
# 子弹类 
class Bullet(pygame.sprite.Sprite): 
    def __init__(self, x, y):
        super().__init__()
        self.image  = bullet_img
        self.rect  = self.image.get_rect(center=(x,  y))
        self.speed  = 10
        hit_sound.play()
 
    def update(self):
        self.rect.y  -= self.speed 
        if self.rect.bottom  < 0:
            self.kill() 

# 爆炸动画类
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 创建爆炸图形（黄色圆形）
        self.image = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 200, 0, 255), (40, 40), 40)
        pygame.draw.circle(self.image, (255, 100, 0, 200), (40, 40), 30)
        self.rect = self.image.get_rect(center=(x, y))
        self.lifetime = 60  # 显示60帧（1秒）
        self.max_lifetime = 60
    
    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
        else:
            # 爆炸逐渐变小和透明
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            size = int(80 * (self.lifetime / self.max_lifetime))
            temp_image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(temp_image, (255, 200, 0, alpha), (size//2, size//2), size//2)
            self.image = temp_image
            self.rect = self.image.get_rect(center=self.rect.center)
 
# 游戏主循环 
def main():
    # 播放背景音乐（循环）
    bg_music.play(-1) 
    
    # 精灵组
    all_sprites = pygame.sprite.Group() 
    enemies = pygame.sprite.Group() 
    bullets = pygame.sprite.Group() 
    explosions = pygame.sprite.Group() 
    
    player = Player()
    all_sprites.add(player) 
    
    clock = pygame.time.Clock() 
    score = 0
    font = pygame.font.SysFont('arial',  30)
    font_large = pygame.font.SysFont('arial',  80, bold=True)
    
    # 敌机生成计时器
    enemy_spawn_timer = 0
    
    # 游戏状态
    game_over = False
    game_over_time = 0
    game_over_duration = 300  # 5秒（60帧/秒）
    
    running = True
    while running:
        # 事件处理
        for event in pygame.event.get(): 
            if event.type  == pygame.QUIT:
                running = False
            elif event.type  == pygame.KEYDOWN:
                if event.key  == pygame.K_SPACE and not game_over:
                    bullet = player.shoot() 
                    all_sprites.add(bullet) 
                    bullets.add(bullet)
                elif event.key  == pygame.K_ESCAPE:
                    running = False 
        
        # 敌机生成（难度随时间递增）
        enemy_spawn_timer += 1
        if enemy_spawn_timer > max(30, 100 - score//10):
            enemy = Enemy()
            all_sprites.add(enemy) 
            enemies.add(enemy) 
            enemy_spawn_timer = 0
        
        # 更新
        if not game_over:
            all_sprites.update() 
        else:
            explosions.update()
            game_over_time += 1
        
        # 碰撞检测
        hits = pygame.sprite.groupcollide(bullets,  enemies, True, True)
        for hit in hits:
            explosion_sound.play() 
            score += 10
        
        # 玩家与敌机碰撞
        if not game_over and pygame.sprite.spritecollide(player,  enemies, False):
            game_over = True
            game_over_time = 0
            explosion_sound.play()
            # 在玩家位置创建爆炸
            explosion = Explosion(player.rect.centerx, player.rect.centery)
            explosions.add(explosion)
            all_sprites.add(explosion)
            # 移除玩家
            player.kill()
        
        # 渲染
        screen.fill(BLACK) 
        all_sprites.draw(screen) 
        explosions.draw(screen)
        
        # 显示分数 
        score_text = font.render(f"Score:  {score}", True, WHITE)
        screen.blit(score_text,  (10, 10))
        
        # 显示Game Over界面
        if game_over:
            # 半透明黑色覆盖层
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(150)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            # 显示Game Over文本
            game_over_text = font_large.render("Game Over", True, RED)
            text_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            screen.blit(game_over_text, text_rect)
            
            # 显示最终分数
            final_score_text = font.render(f"Final Score: {score}", True, WHITE)
            score_rect = final_score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            screen.blit(final_score_text, score_rect)
            
            # 显示倒计时
            remaining = max(0, game_over_duration - game_over_time)
            countdown = remaining // 60 + 1
            countdown_text = font.render(f"退出游戏中... {countdown}", True, WHITE)
            countdown_rect = countdown_text.get_rect(center=(WIDTH//2, HEIGHT - 100))
            screen.blit(countdown_text, countdown_rect)
            
            # 时间到则退出
            if game_over_time >= game_over_duration:
                running = False
        
        pygame.display.flip() 
        clock.tick(60) 
    
    pygame.quit() 
    sys.exit() 
 
if __name__ == "__main__":
    main()