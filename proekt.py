import arcade
import math
import random
import os

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_TITLE = "PYLINE MIAMI"
COLORS = [(255,105,180,255),(255,0,77,255),(0,255,64,255),(0,149,255,255),(191,0,255,255)]

class Player:
    player_textures = []
    textures_loaded = False
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.current_texture = 0
        self.animation_timer = 0
        self.animation_speed = 0.1
        self.direction = 0
        self.is_moving = False
        self.size = 64
        self.hitbox_size = 32
        
        if not Player.textures_loaded:
            for i in range(1, 13):
                if os.path.exists(f"glav/personaje{i}.png"):
                    Player.player_textures.append(arcade.load_texture(f"glav/personaje{i}.png"))
            Player.textures_loaded = True
    
    def move(self, dx, dy, walls):
        old_x, old_y = self.x, self.y
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        
        can_move_x = True
        can_move_y = True
        
        for wall in walls:
            if wall.check_collide(new_x, self.y, self.hitbox_size, self.hitbox_size):
                can_move_x = False
            if wall.check_collide(self.x, new_y, self.hitbox_size, self.hitbox_size):
                can_move_y = False
        
        if can_move_x:
            self.x = new_x
        if can_move_y:
            self.y = new_y
            
        self.x = max(self.hitbox_size//2, min(SCREEN_WIDTH - self.hitbox_size//2, self.x))
        self.y = max(self.hitbox_size//2, min(SCREEN_HEIGHT - self.hitbox_size//2, self.y))
        
        if dx > 0:
            self.direction = 3
        elif dx < 0:
            self.direction = 2
        elif dy > 0:
            self.direction = 0
        elif dy < 0:
            self.direction = 1
            
        self.is_moving = (old_x != self.x or old_y != self.y)
    
    def take_damage(self, dmg):
        self.health -= dmg
        return self.health <= 0
    
    def update_animation(self, delta_time):
        if self.is_moving and len(Player.player_textures) > 0:
            self.animation_timer += delta_time
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_texture = (self.current_texture + 1) % len(Player.player_textures)
        else:
            self.current_texture = 0
    
    def draw(self):
        if Player.player_textures and len(Player.player_textures) > 0:
            texture = Player.player_textures[self.current_texture]
            arcade.draw_texture_rect(texture, arcade.LBWH(self.x - self.size//2, self.y - self.size//2, self.size, self.size))
        else:
            colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
            arcade.draw_lrbt_rectangle_filled(self.x - self.hitbox_size//2, self.x + self.hitbox_size//2, 
                                            self.y - self.hitbox_size//2, self.y + self.hitbox_size//2, colors[self.direction])
        
        health_width = (self.health / self.max_health) * self.hitbox_size
        arcade.draw_lrbt_rectangle_filled(self.x - self.hitbox_size//2, self.x - self.hitbox_size//2 + health_width, 
                                        self.y - self.hitbox_size//2 - 5, self.y - self.hitbox_size//2 - 2, (0, 255, 0, 255))
    
    def get_hitbox(self):
        return (self.x - self.hitbox_size//2, self.x + self.hitbox_size//2, 
                self.y - self.hitbox_size//2, self.y + self.hitbox_size//2)

class EnemyBullet:
    bullet_texture = None
    texture_loaded = False
    
    def __init__(self, x, y, target_x, target_y, damage=100):
        self.x = x
        self.y = y
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx*dx + dy*dy) or 1
        self.dx = dx / dist
        self.dy = dy / dist
        self.speed = 8
        self.active = True
        self.damage = damage
        self.size = 16
        
        if not EnemyBullet.texture_loaded:
            if os.path.exists("bullet2.png"):
                EnemyBullet.bullet_texture = arcade.load_texture("bullet2.png")
            EnemyBullet.texture_loaded = True
    
    def update(self, walls):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        
        for wall in walls:
            if wall.check_collide(self.x, self.y, self.size, self.size):
                self.active = False
                return
        
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT:
            self.active = False
    
    def draw(self):
        if self.active:
            if EnemyBullet.bullet_texture:
                arcade.draw_texture_rect(EnemyBullet.bullet_texture, arcade.LBWH(self.x - self.size//2, self.y - self.size//2, self.size, self.size))
            else:
                arcade.draw_circle_filled(self.x, self.y, 4, (255, 50, 50, 255))
    
    def get_hitbox(self):
        return (self.x - self.size//2, self.x + self.size//2,
                self.y - self.size//2, self.y + self.size//2)

class Enemy:
    enemy_textures = {"normal": [], "shooter": []}
    textures_loaded = False
    
    def __init__(self, x, y, color, etype="normal"):
        self.x = x
        self.y = y
        self.speed = 2
        self.color = color
        self.alive = True
        self.health = 200
        self.max_health = 200
        self.etype = etype
        self.move_timer = 0
        self.attack_timer = 0
        self.shoot_timer = 0
        self.move_dir = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
        self.has_gun = False
        self.spawn_x = x
        self.spawn_y = y
        self.current_texture = 0
        self.animation_timer = 0
        self.animation_speed = 0.15
        self.size = 64
        self.hitbox_size = 32
        self.last_player_pos = (x, y)
        self.patrol_points = []
        self.current_patrol = 0
        self.is_moving = False
        
        if etype == "shooter":
            self.health = 200
            self.max_health = 200
            self.speed = 2.5
            self.has_gun = True
        elif etype == "normal":
            self.health = 200
            self.max_health = 200
            self.speed = 4
            self.has_gun = False
        
        if not Enemy.textures_loaded:
            for i in range(0, 18):
                if os.path.exists(f"vragi/Golem_02_Walking_0{i}.png"):
                    Enemy.enemy_textures["normal"].append(arcade.load_texture(f"vragi/Golem_02_Walking_0{i}.png"))
            for i in range(0, 12):
                if os.path.exists(f"shooter/Wraith_02_Moving Forward_0{i}.png"):
                    Enemy.enemy_textures["shooter"].append(arcade.load_texture(f"shooter/Wraith_02_Moving Forward_0{i}.png"))
            Enemy.textures_loaded = True
    
    def update_animation(self, delta_time):
        if self.is_moving and len(Enemy.enemy_textures[self.etype]) > 0:
            self.animation_timer += delta_time
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_texture = (self.current_texture + 1) % len(Enemy.enemy_textures[self.etype])
        else:
            self.current_texture = 0
    
    def update(self, player_x, player_y, walls, enemy_bullets):
        if not self.alive:
            return 0
            
        self.move_timer += 1
        self.attack_timer += 1
        self.shoot_timer += 1
        
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 400:
            self.last_player_pos = (player_x, player_y)
        
        old_x, old_y = self.x, self.y
        
        if self.has_gun and self.shoot_timer > 30 and dist < 500:
            if random.random() < 0.6:
                bullet_dx = player_x - self.x
                bullet_dy = player_y - self.y
                enemy_bullets.append(EnemyBullet(self.x, self.y, 
                                                player_x + bullet_dx * 0.5, 
                                                player_y + bullet_dy * 0.5, 
                                                100))
                self.shoot_timer = 0
        
        if dist < 300:
            if self.has_gun:
                if dist < 150:
                    dx = -(dx / dist) * self.speed * 1.5
                    dy = -(dy / dist) * self.speed * 1.5
                else:
                    angle = math.atan2(dy, dx) + math.pi/2
                    dx = math.cos(angle) * self.speed
                    dy = math.sin(angle) * self.speed
            else:
                if dist > 50:
                    dx = (dx / dist) * self.speed * 1.5
                    dy = (dy / dist) * self.speed * 1.5
                else:
                    if self.attack_timer > 20:
                        self.attack_timer = 0
                        return 100
            
            new_x = self.x + dx
            new_y = self.y + dy
            
            can_move = True
            for wall in walls:
                if wall.check_collide(new_x, new_y, self.hitbox_size, self.hitbox_size):
                    can_move = False
                    break
            
            if can_move:
                self.x = new_x
                self.y = new_y
        else:
            if self.move_timer > 60:
                self.move_timer = 0
                if dist < 500:
                    target_x, target_y = self.last_player_pos
                else:
                    if len(self.patrol_points) == 0:
                        for _ in range(4):
                            self.patrol_points.append((
                                self.spawn_x + random.randint(-150, 150),
                                self.spawn_y + random.randint(-150, 150)
                            ))
                    target_x, target_y = self.patrol_points[self.current_patrol]
                    self.current_patrol = (self.current_patrol + 1) % len(self.patrol_points)
                
                dx = target_x - self.x
                dy = target_y - self.y
                patrol_dist = math.sqrt(dx*dx + dy*dy)
                if patrol_dist > 10:
                    self.move_dir = (dx / patrol_dist, dy / patrol_dist)
            
            new_x = self.x + self.move_dir[0] * self.speed
            new_y = self.y + self.move_dir[1] * self.speed
            
            can_move = True
            for wall in walls:
                if wall.check_collide(new_x, new_y, self.hitbox_size, self.hitbox_size):
                    can_move = False
                    break
            
            if can_move:
                self.x = new_x
                self.y = new_y
        
        self.x = max(self.hitbox_size//2, min(SCREEN_WIDTH - self.hitbox_size//2, self.x))
        self.y = max(self.hitbox_size//2, min(SCREEN_HEIGHT - self.hitbox_size//2, self.y))
        
        self.is_moving = (old_x != self.x or old_y != self.y)
        
        return 0
    
    def take_damage(self, dmg):
        self.health -= dmg
        if self.health <= 0:
            self.alive = False
            return True
        return False
    
    def draw(self):
        if self.alive:
            textures = Enemy.enemy_textures.get(self.etype, [])
            if textures and len(textures) > 0:
                texture = textures[self.current_texture]
                arcade.draw_texture_rect(texture, arcade.LBWH(self.x - self.size//2, self.y - self.size//2, self.size, self.size))
            else:
                arcade.draw_lrbt_rectangle_filled(self.x - self.hitbox_size//2, self.x + self.hitbox_size//2, 
                                                self.y - self.hitbox_size//2, self.y + self.hitbox_size//2, self.color)
            
            health_width = (self.health / self.max_health) * self.hitbox_size
            arcade.draw_lrbt_rectangle_filled(self.x - self.hitbox_size//2, self.x - self.hitbox_size//2 + health_width, 
                                            self.y - self.hitbox_size//2 - 5, self.y - self.hitbox_size//2 - 2, (255, 0, 0, 255))
    
    def get_hitbox(self):
        return (self.x - self.hitbox_size//2, self.x + self.hitbox_size//2, 
                self.y - self.hitbox_size//2, self.y + self.hitbox_size//2)

class Bullet:
    bullet_texture = None
    texture_loaded = False
    
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx*dx + dy*dy) or 1
        self.dx = dx / dist
        self.dy = dy / dist
        self.speed = 15
        self.active = True
        self.damage = 100
        self.size = 16
        
        if not Bullet.texture_loaded:
            if os.path.exists("bullet.png"):
                Bullet.bullet_texture = arcade.load_texture("bullet.png")
            Bullet.texture_loaded = True
    
    def update(self, walls):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        
        for wall in walls:
            if wall.check_collide(self.x, self.y, self.size, self.size):
                self.active = False
                return
        
        if self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT:
            self.active = False
    
    def draw(self):
        if self.active:
            if Bullet.bullet_texture:
                arcade.draw_texture_rect(Bullet.bullet_texture, arcade.LBWH(self.x - self.size//2, self.y - self.size//2, self.size, self.size))
            else:
                arcade.draw_circle_filled(self.x, self.y, 4, (255, 255, 0, 255))
    
    def get_hitbox(self):
        return (self.x - self.size//2, self.x + self.size//2,
                self.y - self.size//2, self.y + self.size//2)

class Wall:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    
    def check_collide(self, x, y, w, h):
        return (x - w//2 < self.x + self.w//2 and
                x + w//2 > self.x - self.w//2 and
                y - h//2 < self.y + self.h//2 and
                y + h//2 > self.y - self.h//2)
    
    def draw(self):
        arcade.draw_lrbt_rectangle_filled(self.x - self.w//2, self.x + self.w//2, self.y - self.h//2, self.y + self.h//2, (80, 80, 80, 255))
        arcade.draw_lrbt_rectangle_outline(self.x - self.w//2, self.x + self.w//2, self.y - self.h//2, self.y + self.h//2, (180, 180, 180, 255), 2)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.size = random.uniform(2, 5)
        self.color = color
        self.life = 20
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0
    
    def draw(self):
        alpha = int((self.life / 20) * 255)
        color = list(self.color)
        color[3] = alpha
        arcade.draw_circle_filled(self.x, self.y, self.size, color)

class BloodEffect:
    blood_textures = []
    textures_loaded = False
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.current_texture = 0
        self.animation_timer = 0
        self.animation_speed = 0.005
        self.active = True
        self.lifetime = 0.5
        self.timer = 0
        
        if not BloodEffect.textures_loaded:
            for i in range(0, 28):
                if os.path.exists(f"png/{i}.png"):
                    BloodEffect.blood_textures.append(arcade.load_texture(f"png/{i}.png"))
            BloodEffect.textures_loaded = True
    
    def update(self, delta_time):
        if not self.active:
            return
        
        self.timer += delta_time
        if self.timer >= self.lifetime:
            self.active = False
            return
            
        self.animation_timer += delta_time
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_texture = (self.current_texture + 1) % len(BloodEffect.blood_textures)
    
    def draw(self):
        if self.active and BloodEffect.blood_textures and len(BloodEffect.blood_textures) > 0:
            texture = BloodEffect.blood_textures[self.current_texture]
            size = 128
            arcade.draw_texture_rect(texture, arcade.LBWH(self.x - size//2, self.y - size//2, size, size))

class Level(arcade.View):
    def __init__(self, level_num, menu):
        super().__init__()
        self.level = level_num
        self.menu = menu
        self.player = None
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.walls = []
        self.particles = []
        self.blood_effects = []
        self.score = 0
        self.kills = 0
        self.game_over = False
        self.win = False
        self.keys = [False, False, False, False]
        self.mouse_x = 0
        self.mouse_y = 0
        self.shoot_timer = 0
        self.shoot_delay = 10
        self.damage_cooldown = 0
        self.show_message = False
        self.message_timer = 0
        
        self.setup_level()
    
    def is_valid_spawn(self, x, y, w, h, walls, check_enemies=True):
        for wall in walls:
            if wall.check_collide(x, y, w, h):
                return False
        
        if check_enemies:
            for enemy in self.enemies:
                if abs(enemy.x - x) < 50 and abs(enemy.y - y) < 50:
                    return False
        
        return True
    
    def try_spawn_enemy(self, x, y, etype):
        if self.is_valid_spawn(x, y, 32, 32, self.walls, True):
            self.enemies.append(Enemy(x, y, COLORS[len(self.enemies)%len(COLORS)], etype))
            return True
        return False
    
    def setup_level(self):
        self.enemies = []
        self.walls = []
        self.game_over = False
        self.win = False
        self.show_message = False
        
        base_walls = [
            Wall(600, 30, 1200, 40),
            Wall(600, 770, 1200, 40),
            Wall(30, 400, 40, 800),
            Wall(1170, 400, 40, 800),
        ]
        self.walls.extend(base_walls)
        
        if self.level == 1:
            self.walls.extend([
                Wall(200, 650, 20, 200),
                Wall(460, 650, 20, 200),
                Wall(200, 300, 20, 300),
                Wall(460, 300, 20, 300),
                Wall(130, 450, 160, 25),
                Wall(800, 450, 700, 25),
                Wall(800, 650, 20, 200),
            ])
            
            self.player = Player(350, 100)
            
            enemy_positions = [
                (100, 400, "normal"), (500, 400, "normal"), (800, 400, "normal"),
                (800, 100, "shooter"), (100, 700, "shooter"), (500, 700, "normal"),
                (1000, 700, "shooter"), (1000, 600, "normal"), (300, 500, "shooter"),
                (700, 300, "normal"),
            ]
            
        elif self.level == 2:
            self.walls.extend([
                Wall(400, 500, 200, 20), Wall(400, 300, 200, 20),
                Wall(800, 500, 200, 20), Wall(800, 300, 200, 20),
                Wall(200, 400, 20, 300), Wall(1000, 400, 20, 300),
                Wall(600, 150, 400, 20), Wall(600, 650, 400, 20),
                Wall(300, 200, 20, 150), Wall(900, 200, 20, 150),
                Wall(300, 600, 20, 150), Wall(900, 600, 20, 150),
            ])
            
            self.player = Player(100, 400)
            
            enemy_positions = [
                (400, 400, "shooter"), (800, 400, "shooter"), (300, 250, "normal"),
                (900, 250, "normal"), (300, 550, "normal"), (900, 550, "normal"),
                (200, 150, "shooter"), (1000, 150, "shooter"), (200, 650, "shooter"),
                (1000, 650, "shooter"), (500, 200, "normal"), (700, 600, "normal"),
            ]
            
        elif self.level == 3:
            self.walls.extend([
                Wall(300, 500, 20, 400), Wall(500, 500, 20, 400),
                Wall(700, 500, 20, 400), Wall(900, 500, 20, 400),
                Wall(200, 300, 400, 20), Wall(600, 300, 400, 20),
                Wall(400, 200, 20, 200), Wall(800, 200, 20, 200),
                Wall(400, 600, 20, 200), Wall(800, 600, 20, 200),
                Wall(150, 150, 200, 20), Wall(1050, 150, 200, 20),
                Wall(150, 650, 200, 20), Wall(1050, 650, 200, 20),
            ])
            
            self.player = Player(600, 400)
            
            enemy_positions = [
                (200, 200, "shooter"), (400, 200, "shooter"), (600, 200, "shooter"),
                (800, 200, "shooter"), (1000, 200, "shooter"), (200, 600, "shooter"),
                (400, 600, "shooter"), (600, 600, "shooter"), (800, 600, "shooter"),
                (1000, 600, "shooter"), (300, 400, "normal"), (500, 400, "normal"),
                (700, 400, "normal"), (900, 400, "normal"),
            ]
        
        for x, y, etype in enemy_positions:
            self.try_spawn_enemy(x, y, etype)
    
    def on_show(self):
        self.window.background_color = (0,0,0)
        self.game_over = False
        self.win = False
        self.show_message = False
    
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
    
    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        
        bg = [(20,20,40), (40,20,20), (20,40,20)]
        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, bg[self.level-1])
        
        for i in range(0, w, 50):
            for j in range(0, h, 50):
                arcade.draw_lrbt_rectangle_outline(i - 25, i + 25, j - 25, j + 25, (255,255,255,20), 1)
        
        for wall in self.walls:
            wall.draw()
        
        for blood in self.blood_effects:
            blood.draw()
        
        for particle in self.particles:
            particle.draw()
        
        for enemy in self.enemies:
            enemy.draw()
        
        for bullet in self.enemy_bullets:
            bullet.draw()
        
        for bullet in self.bullets:
            bullet.draw()
        
        if self.player:
            self.player.draw()
            arcade.draw_line(self.player.x, self.player.y, self.mouse_x, self.mouse_y, COLORS[0], 1)
        
        alive_enemies = len([e for e in self.enemies if e.alive])
        arcade.draw_text(f"УРОВЕНЬ {self.level}", 100, h-50, COLORS[self.level-1], 24, bold=True)
        arcade.draw_text(f"ВРАГОВ: {alive_enemies}", 100, h-80, (255,255,255), 18)
        arcade.draw_text(f"УБИТО: {self.kills}", 100, h-110, (255,255,255), 18)
        
        if self.game_over:
            arcade.draw_text("ТЫ УМЕР", w//2, h//2, (255,0,0), 72, anchor_x="center", anchor_y="center", bold=True)
            arcade.draw_text("R - заново | ESC - меню", w//2, h//2-70, (255,255,255), 24, anchor_x="center")
        elif self.win:
            arcade.draw_text("УРОВЕНЬ ПРОЙДЕН!", w//2, h//2, (0,255,0), 72, anchor_x="center", anchor_y="center", bold=True)
            arcade.draw_text("ПРОБЕЛ - дальше | ESC - меню", w//2, h//2-70, (255,255,255), 24, anchor_x="center")
    
    def on_update(self, dt):
        if self.game_over or self.win:
            return
        
        if self.player:
            self.player.update_animation(dt)
        
        for enemy in self.enemies:
            if enemy.alive:
                enemy.update_animation(dt)
        
        for blood in self.blood_effects[:]:
            blood.update(dt)
            if not blood.active:
                self.blood_effects.remove(blood)
            
        self.shoot_timer += 1
        self.damage_cooldown -= 1
        
        dx, dy = 0, 0
        if self.keys[0]: dy = 1
        if self.keys[1]: dy = -1
        if self.keys[2]: dx = -1
        if self.keys[3]: dx = 1
        
        if dx != 0 or dy != 0:
            if dx != 0 and dy != 0:
                dx *= 0.7
                dy *= 0.7
            self.player.move(dx, dy, self.walls)
        
        for enemy in self.enemies[:]:
            if enemy.alive:
                damage = enemy.update(self.player.x, self.player.y, self.walls, self.enemy_bullets)
                if damage > 0 and self.damage_cooldown <= 0:
                    if self.player.take_damage(damage):
                        self.game_over = True
                        return
                    self.damage_cooldown = 20
                    for _ in range(5):
                        self.particles.append(Particle(self.player.x, self.player.y, (255,0,0,255)))
        
        for bullet in self.enemy_bullets[:]:
            bullet.update(self.walls)
            
            if self.player:
                bx1, bx2, by1, by2 = bullet.get_hitbox()
                px1, px2, py1, py2 = self.player.get_hitbox()
                
                if (bx1 < px2 and bx2 > px1 and by1 < py2 and by2 > py1):
                    if self.damage_cooldown <= 0:
                        if self.player.take_damage(bullet.damage):
                            self.game_over = True
                            return
                        self.damage_cooldown = 20
                        for _ in range(5):
                            self.particles.append(Particle(self.player.x, self.player.y, (255,0,0,255)))
                    bullet.active = False
            
            if not bullet.active:
                self.enemy_bullets.remove(bullet)
        
        for bullet in self.bullets[:]:
            bullet.update(self.walls)
            
            for enemy in self.enemies:
                if enemy.alive:
                    bx1, bx2, by1, by2 = bullet.get_hitbox()
                    ex1, ex2, ey1, ey2 = enemy.get_hitbox()
                    
                    if (bx1 < ex2 and bx2 > ex1 and by1 < ey2 and by2 > ey1):
                        if enemy.take_damage(bullet.damage):
                            self.kills += 1
                            self.score += 100
                            self.blood_effects.append(BloodEffect(enemy.x, enemy.y))
                            
                            try:
                                s = arcade.Sound(":resources:sounds/hit3.wav")
                                s.play(volume=0.1)
                            except:
                                pass
                        
                        bullet.active = False
                        break
            
            if not bullet.active:
                self.bullets.remove(bullet)
        
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)
        
        alive_enemies = len([e for e in self.enemies if e.alive])
        if alive_enemies == 0 and len(self.enemies) > 0:
            self.win = True
            self.menu.save(self.level)
            
            for _ in range(30):
                self.particles.append(Particle(self.player.x, self.player.y, (0,255,0,255)))
    
    def on_key_press(self, key, mods):
        if key == arcade.key.W:
            self.keys[0] = True
        elif key == arcade.key.S:
            self.keys[1] = True
        elif key == arcade.key.A:
            self.keys[2] = True
        elif key == arcade.key.D:
            self.keys[3] = True
        
        elif key == arcade.key.R and self.game_over:
            self.setup_level()
            self.game_over = False
            self.win = False
            self.kills = 0
            self.enemy_bullets = []
            
        elif key == arcade.key.SPACE and self.win:
            if self.level < 3:
                self.window.show_view(Level(self.level + 1, self.menu))
            else:
                self.window.show_view(self.menu)
                
        elif key == arcade.key.ESCAPE:
            self.window.show_view(self.menu)
    
    def on_key_release(self, key, mods):
        if key == arcade.key.W:
            self.keys[0] = False
        elif key == arcade.key.S:
            self.keys[1] = False
        elif key == arcade.key.A:
            self.keys[2] = False
        elif key == arcade.key.D:
            self.keys[3] = False
    
    def on_mouse_press(self, x, y, button, mods):
        if button == arcade.MOUSE_BUTTON_LEFT and not self.game_over and not self.win:
            if self.shoot_timer >= self.shoot_delay:
                self.bullets.append(Bullet(self.player.x, self.player.y, x, y))
                self.shoot_timer = 0
                
                try:
                    s = arcade.Sound(":resources:sounds/laser1.wav")
                    s.play(volume=0.1)
                except:
                    pass

class Menu(arcade.View):
    def __init__(self):
        super().__init__()
        self.t = 0
        self.c = 0
        self.show_levels = False
        self.max_level = 1
        self.passed = [False, False, False]
        self.mx = 0
        self.my = 0
        self.music = None
        self.current = None
        self.bg = None
        
        if os.path.exists("lobby1.jpg"):
            self.bg = arcade.load_texture("lobby1.jpg")
        
        if os.path.exists("save.dat"):
            with open("save.dat", "r") as f:
                data = f.read().split()
                self.max_level = int(data[0])
                self.passed = [bool(int(x)) for x in data[1:4]]
        
        tracks = ["hotline_miami2.mp3", "hotline_miami3.mp3"]
        for track in tracks:
            if os.path.exists(track):
                self.current = track
                self.music = arcade.Sound(self.current, streaming=True)
                self.music.play(volume=0.15)
                arcade.schedule(self.check_music, 1.0)
                break
    
    def check_music(self, dt):
        if self.music and not self.music.is_playing:
            self.next_track()
    
    def next_track(self):
        tracks = ["hotline_miami2.mp3", "hotline_miami3.mp3"]
        avail = [t for t in tracks if t != self.current and os.path.exists(t)]
        if avail:
            self.current = random.choice(avail)
            self.music = arcade.Sound(self.current, streaming=True)
            self.music.play(volume=0.15)

    def save(self, level):
        if 1 <= level <= 3:
            self.passed[level-1] = True
            if level == self.max_level and self.max_level < 3:
                self.max_level += 1
            with open("save.dat", "w") as f:
                f.write(f"{self.max_level} " + " ".join(["1" if x else "0" for x in self.passed]))
    
    def on_show(self):
        self.window.background_color = (0,0,0)
    
    def on_hide(self):
        if self.music:
            self.music.stop()
        arcade.unschedule(self.check_music)
    
    def on_mouse_motion(self, x, y, dx, dy):
        self.mx = x
        self.my = y
    
    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        
        if self.bg:
            arcade.draw_texture_rect(self.bg, arcade.LBWH(0, 0, w, h))
        else:
            arcade.draw_lrbt_rectangle_filled(0, w, 0, h, (0,0,0,255))
        
        self.t += 0.02
        self.c += 0.01
        
        title = "PYLINE MIAMI"
        size = int(min(72, h * 0.09))
        arcade.draw_text(title, w//2, h*0.8 + math.sin(self.t)*3, 
                        COLORS[int(self.c)%len(COLORS)], size, anchor_x="center", anchor_y="center", bold=True)
        
        if self.show_levels:
            arcade.draw_text("ВЫБЕРИТЕ УРОВЕНЬ", w//2, h*0.7, (255,255,255), 36, anchor_x="center", anchor_y="center", bold=True)
            
            for i in range(3):
                x = w//2 + (i-1)*250
                y = h//2
                unlocked = i+1 <= self.max_level
                
                if not unlocked:
                    bg = (30, 30, 30, 200)
                    status = "ЗАКРЫТ"
                elif self.passed[i]:
                    bg = (0, 180, 0, 200)
                    status = "ПРОЙДЕНО"
                else:
                    bg = (80, 80, 80, 200)
                    status = "ОТКРЫТ"
                
                hover = (x-100 <= self.mx <= x+100 and y-30 <= self.my <= y+30 and unlocked)
                
                if hover:
                    bg = COLORS[int(self.t*2)%len(COLORS)]
                    mult = 1.2
                else:
                    mult = 1.0
                
                arcade.draw_lrbt_rectangle_filled(x - 100*mult, x + 100*mult, y - 30*mult, y + 30*mult, bg)
                arcade.draw_lrbt_rectangle_outline(x - 100*mult, x + 100*mult, y - 30*mult, y + 30*mult, (255,255,255), 2)
                
                txt_color = (255,255,255) if unlocked else (100,100,100)
                arcade.draw_text(f"{i+1}", x, y+5, txt_color, 20, anchor_x="center", anchor_y="center", bold=True)
                arcade.draw_text(status, x, y-15, txt_color, 12, anchor_x="center", anchor_y="center")
            
            back_x, back_y = w//2, 150
            back_hover = (back_x-75 <= self.mx <= back_x+75 and back_y-20 <= self.my <= back_y+20)
            
            if back_hover:
                back_color = COLORS[int(self.t*2)%len(COLORS)]
            else:
                back_color = (150, 150, 150, 200)
            
            arcade.draw_lrbt_rectangle_filled(back_x - 75, back_x + 75, back_y - 20, back_y + 20, back_color)
            arcade.draw_lrbt_rectangle_outline(back_x - 75, back_x + 75, back_y - 20, back_y + 20, (255,255,255), 2)
            arcade.draw_text("НАЗАД", back_x, back_y, (0,0,0) if back_hover else (255,255,255), 20, anchor_x="center", anchor_y="center", bold=True)
            
        else:
            play_x, play_y = w//2, h//2 + 30
            play_hover = (play_x-125 <= self.mx <= play_x+125 and play_y-25 <= self.my <= play_y+25)
            
            if play_hover:
                play_color = COLORS[int(self.t*2)%len(COLORS)]
            else:
                play_color = (150, 150, 150, 200)
            
            arcade.draw_lrbt_rectangle_filled(play_x - 125, play_x + 125, play_y - 25, play_y + 25, play_color)
            arcade.draw_lrbt_rectangle_outline(play_x - 125, play_x + 125, play_y - 25, play_y + 25, (255,255,255), 3)
            arcade.draw_text("ИГРАТЬ", play_x, play_y, (0,0,0) if play_hover else (255,255,255), 24, anchor_x="center", anchor_y="center", bold=True)
            
            exit_x, exit_y = w//2, h//2 - 50
            exit_hover = (exit_x-125 <= self.mx <= exit_x+125 and exit_y-25 <= self.my <= exit_y+25)
            
            if exit_hover:
                exit_color = COLORS[int(self.t*2)%len(COLORS)]
            else:
                exit_color = (150, 150, 150, 200)
            
            arcade.draw_lrbt_rectangle_filled(exit_x - 125, exit_x + 125, exit_y - 25, exit_y + 25, exit_color)
            arcade.draw_lrbt_rectangle_outline(exit_x - 125, exit_x + 125, exit_y - 25, exit_y + 25, (255,255,255), 3)
            arcade.draw_text("ВЫХОД", exit_x, exit_y, (0,0,0) if exit_hover else (255,255,255), 24, anchor_x="center", anchor_y="center", bold=True)
    
    def on_mouse_press(self, x, y, button, mods):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        
        w, h = self.window.width, self.window.height
        
        if self.show_levels:
            for i in range(3):
                bx = w//2 + (i-1)*250
                by = h//2
                unlocked = i+1 <= self.max_level
                
                if (bx-100 <= x <= bx+100 and by-30 <= y <= by+30 and unlocked):
                    self.window.show_view(Level(i+1, self))
                    return
            
            if (w//2-75 <= x <= w//2+75 and 150-20 <= y <= 150+20):
                self.show_levels = False
        else:
            if (w//2-125 <= x <= w//2+125 and h//2+30-25 <= y <= h//2+30+25):
                self.show_levels = True
            elif (w//2-125 <= x <= w//2+125 and h//2-50-25 <= y <= h//2-50+25):
                arcade.exit()
    
    def on_key_press(self, key, mods):
        if key == arcade.key.ESCAPE:
            if self.show_levels:
                self.show_levels = False
            else:
                arcade.exit()
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    window.show_view(Menu())
    arcade.run()

if __name__ == "__main__":
    main()
