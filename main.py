import pygame
import random
import os


FPS: int = 60
WHITE: tuple[int, int, int] = (255, 255, 255)
BLACK: tuple[int, int, int] = (0, 0, 0)
GREEN: tuple[int, int, int] = (0, 255, 0)
RED: tuple[int, int, int] = (255, 0, 0)
YELLOW: tuple[int, int, int] = (255, 255, 0)
WIDTH: int = 800
HEIGHT: int = 600

# 遊戲初始化、創建視窗
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("太空生存戰")
clock = pygame.time.Clock()

# 載入圖片
img_dir_path = "img"
background_img = pygame.image.load(os.path.join(img_dir_path, "background.png"))
player_img = pygame.image.load(os.path.join(img_dir_path, "player.png"))
player_mini_img = pygame.transform.scale(player_img, (25, 19))
pygame.display.set_icon(player_img)
rock_imgs = []
for i in range(7):
    rock_imgs.append(pygame.image.load(os.path.join(img_dir_path, f"rock{i}.png")))
bullet_img = pygame.image.load(os.path.join(img_dir_path, "bullet.png"))
expl_anim: dict[str, list] = {
    'large': [],
    'small': [],
    'player': []
}
for i in range(9):
    expl_img = pygame.image.load(os.path.join(img_dir_path, f"expl{i}.png"))
    expl_anim['large'].append(pygame.transform.scale(expl_img, (75, 75)))
    expl_anim['small'].append(pygame.transform.scale(expl_img, (30, 30)))
    player_expl_img = pygame.image.load(os.path.join(img_dir_path, f"player_expl{i}.png"))
    expl_anim['player'].append(player_expl_img)
power_img = {
    'shield': pygame.image.load(os.path.join(img_dir_path, "shield.png")),
    'gun': pygame.image.load(os.path.join(img_dir_path, "gun.png"))
}

# 載入音樂、音效
sound_dir_path = "sound"
shoot_sound = pygame.mixer.Sound(os.path.join(sound_dir_path, "shoot.wav"))
gun_sound = pygame.mixer.Sound(os.path.join(sound_dir_path, "pow0.wav"))
shield_sound = pygame.mixer.Sound(os.path.join(sound_dir_path, "pow1.wav"))
die_sound = pygame.mixer.Sound(os.path.join(sound_dir_path, "rumble.ogg"))
expl_sounds = [
    pygame.mixer.Sound(os.path.join(sound_dir_path, "expl0.wav")),
    pygame.mixer.Sound(os.path.join(sound_dir_path, "expl1.wav"))
]
pygame.mixer.music.load(os.path.join(sound_dir_path, "background.ogg"))
pygame.mixer.music.set_volume(0.4)

font_name = os.path.join("font.ttf")

pygame.mixer.music.play(-1)

def draw_text(surf, text: str, size: int, x: int, y: int):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface, text_rect)

def new_rock() -> None:
    rock = Rock()
    all_sprites.add(rock)
    rocks.add(rock)

def draw_health(surf, hp: int, x: int, y: int) -> None:
    if hp < 0:
        hp = 0
    BAR_LENGTH: int = 100
    BAR_HEIGHT: int = 10
    fill: float = (hp / 100) * BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)

def draw_lives(surf, lives: int, img, x: int, y: int) -> None:
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + (32 * i)
        img_rect.y = y
        surf.blit(img, img_rect)

def draw_init() -> bool:
    screen.fill(BLACK)
    screen.blit(background_img, (0, 0))
    all_sprites.draw(screen)
    draw_text(screen, "太空生存戰！", 64, WIDTH/2, HEIGHT/4)
    draw_text(screen, "用方向鍵或a和d移動飛船，空白鍵發射子彈", 22, WIDTH/2, HEIGHT/2)
    draw_text(screen, "按任意鍵開始遊戲", 18, WIDTH/2, HEIGHT*3/4)
    pygame.display.update()
    waiting: bool = True
    while waiting:
        clock.tick(FPS)
        # 取得輸入
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True
            elif event.type == pygame.KEYUP:
                waiting = False
                return False

class Player(pygame.sprite.Sprite):
    def __init__(self) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(player_img, (50, 38))
        self.rect = self.image.get_rect()
        self.radius = 20
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 15
        self.speedx: int = 8
        self.health: int = 100
        self.lives: int = 3
        self.hidden: bool = False
        self.hide_time: int = 0
        self.gun: int = 1
        self.gun_time: int = 0
    
    def update(self) -> None:
        now = pygame.time.get_ticks()

        if self.gun > 1 and (now - self.gun_time) > 5000:
            self.gun = 1
            self.gun_time = now

        if self.hidden and (now - self.hide_time) > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 10

        key_pressed = pygame.key.get_pressed()
        if key_pressed[pygame.K_RIGHT] or key_pressed[pygame.K_d]:
            self.rect.x += self.speedx
        if key_pressed[pygame.K_LEFT] or key_pressed[pygame.K_a]:
            self.rect.x -= self.speedx
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self) -> None:
        if not(self.hidden):
            match self.gun:
                case 1:
                    bullets_list = [
                        Bullet(self.rect.centerx, self.rect.top)
                    ]
                case 2:
                    bullets_list = [
                        Bullet(self.rect.left, self.rect.centery),
                        Bullet(self.rect.right, self.rect.centery)
                    ]
                case _:
                    bullets_list = [
                        Bullet(self.rect.centerx, self.rect.top),
                        Bullet(self.rect.left, self.rect.centery),
                        Bullet(self.rect.right, self.rect.centery)
                    ]
            for bullet in bullets_list:
                all_sprites.add(bullet)
                bullets.add(bullet)
            shoot_sound.play()
    
    def hide(self) -> None:
        self.hidden = True
        self.hide_time = pygame.time.get_ticks()
        self.rect.center = (WIDTH/2, HEIGHT+500)
    
    def gunup(self) -> None:
        self.gun += 1
        self.gun_time = pygame.time.get_ticks()

class Rock(pygame.sprite.Sprite):
    def __init__(self) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image_ori = random.choice(rock_imgs)
        self.image = self.image_ori.copy()
        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width *0.85 / 2)
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-180, -100)
        self.speedy = random.randrange(2, 10)
        self.speedx = random.randrange(-3, 3)
        self.rot_degree = random.randrange(-3, 3)
        self.total_degree = 0
    
    def rotate(self) -> None:
        self.total_degree += self.rot_degree
        self.total_degree %= 360
        self.image = pygame.transform.rotate(self.image_ori, self.total_degree)
        center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = center

    def update(self) -> None:
        self.rotate()
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if (self.rect.top > HEIGHT) or (self.rect.left > WIDTH) or (self.rect.right < 0):
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(2, 10)
            self.speedx = random.randrange(-3, 3)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -10
    
    def update(self) -> None:
        self.rect.bottom += self.speedy
        if self.rect.bottom < 0:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size: str) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = expl_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50
    
    def update(self) -> None:
        now = pygame.time.get_ticks()
        if (now - self.last_update) > (self.frame_rate):
            self.last_update = now
            self.frame += 1
            if self.frame == len(expl_anim[self.size]):
                self.kill()
            else:
                self.image = expl_anim[self.size][self.frame]
                center = self.rect.center
                self.rect = self.image.get_rect()
                self.rect.center = center

class Power(pygame.sprite.Sprite):
    def __init__(self, center) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(['shield', 'gun'])
        self.image = power_img[self.type]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 3
    
    def update(self) -> None:
        self.rect.bottom += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()


all_sprites = pygame.sprite.Group()
rocks = pygame.sprite.Group()
bullets = pygame.sprite.Group()
powers = pygame.sprite.Group()
player = Player()
all_sprites.add(player)
for i in range(8):
    new_rock()
score: int = 0

# 遊戲迴圈
show_init: bool = True
running: bool = True
while running:
    if show_init:
        close = draw_init()
        if close:
            break
        show_init = False
        all_sprites = pygame.sprite.Group()
        rocks = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        powers = pygame.sprite.Group()
        player = Player()
        all_sprites.add(player)
        for i in range(8):
            new_rock()
        score: int = 0

    clock.tick(FPS)

    # 取得輸入
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # 更新遊戲
    all_sprites.update()
    hits = pygame.sprite.groupcollide(rocks, bullets, True, True)
    for hit in hits:
        random.choice(expl_sounds).play()
        score += hit.radius
        expl = Explosion(hit.rect.center, 'large')
        all_sprites.add(expl)
        if random.random() > 0.9:
            pow = Power(hit.rect.center)
            all_sprites.add(pow)
            powers.add(pow)
        new_rock()
    
    hits = pygame.sprite.spritecollide(player, rocks, True, pygame.sprite.collide_circle)
    for hit in hits:
        new_rock()
        expl = Explosion(hit.rect.center, 'small')
        all_sprites.add(expl)
        player.health -= hit.radius
        if player.health <= 0:
            death_expl = Explosion(player.rect.center, 'player')
            all_sprites.add(death_expl)
            die_sound.play()
            player.lives -= 1
            player.health = 100
            player.hide()
    
    hits = pygame.sprite.spritecollide(player, powers, True)
    for hit in hits:
        match hit.type:
            case 'shield':
                shield_sound.play()
                player.health += 20
                if player.health > 100:
                    player.health = 100
            case 'gun':
                gun_sound.play()
                player.gunup()

    if player.lives == 0 and not(death_expl.alive()):
        show_init = True

    # 畫面顯示
    screen.fill(BLACK)
    screen.blit(background_img, (0, 0))
    all_sprites.draw(screen)
    draw_text(screen, str(score), 30, WIDTH/2, 10)
    draw_health(screen, player.health, 7, 15)
    draw_lives(screen, player.lives, player_mini_img, WIDTH-100, 15)
    pygame.display.update()

pygame.quit()