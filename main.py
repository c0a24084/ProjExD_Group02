import os
import time 
import pygame as pg
import sys
import math
import random 
from typing import Callable, List

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
save_score = 0
save_lv = 0
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def menu():
    """
    メインメニューに関する関数
    """
    pg.init()
    pg.display.set_caption("生きろこうかとん！")
    bg_img = pg.image.load(f"fig/menu_bg.jpg")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    
    fonto1 = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 80)
    txt1 = fonto1.render("生きろこうかとん!", True, (255, 255, 255))
    fonto2 = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 50)
    txt2 = fonto2.render("PRESS SPACE TO START", True, (255, 255, 255))

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                main(screen)
                time.sleep(1)
                GameOver(screen)
                return 0
            
        screen.blit(bg_img, [0, 0])
        screen.blit(txt1, [235, 200])
        screen.blit(txt2, [315, 500])
        pg.display.update()


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird(pg.sprite.Sprite):
    """
    こうかとんの実装に関するクラス
    """

    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy:tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.hp = 3

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Enemy(pg.sprite.Sprite):
    """
    敵キャラのクラス
    """
    def __init__(self, bird: Bird, tmr: int):
        super().__init__()
        self.type = random.randint(0, 2)  # ランダムに種類を変える

        if self.type == 0:
            self.image = pg.transform.rotozoom(pg.image.load("fig/alien1.png"), 0, 0.6)
            self.image.fill((100, 255, 100, 255), special_flags=pg.BLEND_RGBA_MULT)
            self.speed = 2
        elif self.type == 1:
            self.image = pg.transform.rotozoom(pg.image.load("fig/alien2.png"), 0, 0.5)
            self.image.fill((100, 100, 255, 255), special_flags=pg.BLEND_RGBA_MULT)
            self.speed = 3
        else:
            self.image = pg.transform.rotozoom(pg.image.load("fig/alien3.png"), 0, 0.4)
            self.image.fill((255, 100, 100, 255), special_flags=pg.BLEND_RGBA_MULT)
            self.speed = 4

        self.rect = self.image.get_rect()

        # スポーン位置
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            self.rect.center = (random.randint(0, WIDTH), -50)
        elif edge == "bottom":
            self.rect.center = (random.randint(0, WIDTH), HEIGHT + 50)
        elif edge == "left":
            self.rect.center = (-50, random.randint(0, HEIGHT))
        else:
            self.rect.center = (WIDTH + 50, random.randint(0, HEIGHT))

        self.bird = bird
        self.is_frozen = False
        self.freeze_timer = 0
    

    def update(self):
        """
        敵がこうかとんを追従するように設定
        """
        if not self.is_frozen: # 凍結中でなければ移動
            dx = self.bird.rect.centerx - self.rect.centerx
            dy = self.bird.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist != 0:
                dx, dy = dx / dist, dy / dist
            self.rect.move_ip(dx * self.speed, dy * self.speed)
        else: # 凍結中のタイマーを減らす
            self.freeze_timer -= 1
            if self.freeze_timer <= 0:
                self.unfreeze()

    def freeze(self):
        """敵を凍結状態にする"""
        self.is_frozen = True
        self.freeze_timer = 3 * 50 # 3秒 * 50fps = 150フレーム

    def unfreeze(self):
        """敵の凍結状態を解除する"""
        self.is_frozen = False
        self.freeze_timer = 0
# Weaponクラスの前にSpecialShotクラスを追加
 

class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0 = 0, size: float = 1.0, is_special: bool = False):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, size)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10
        self.is_special = is_special

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            if not self.is_special: 
                self.kill()
            elif self.is_special and (self.rect.left > WIDTH + 50 or self.rect.right < -50 or self.rect.top > HEIGHT + 50 or self.rect.bottom < -50):
                self.kill()


class SpecialShot:
    """
    必殺技に関するクラス
    """
    EXP_COST = 100 # 特殊ビーム発射に必要なスコア

    def __init__(self):
        """
        SpecialShotの初期設定を行う
        """
        pass

    def activate(self, bird: "Bird", score: "Score", enemies: pg.sprite.Group, beams: pg.sprite.Group) -> bool:
        """
        特殊ビームを発射し、敵を凍結させる処理を行う。
        発動に成功したらTrue、失敗したらFalseを返す。
        引数 bird: こうかとんインスタンス
        引数 score: スコアインスタンス
        引数 enemies: 敵グループ
        引数 beams: ビームグループ
        """
        if score.value >= SpecialShot.EXP_COST:
            # 特大ビームを発射 (size=3.0, is_special=True)
            beams.add(Beam(bird, 0, 3.0, True))
            score.value -= SpecialShot.EXP_COST # スコアを消費

            # 全ての敵を一定時間停止させる
            for enemy in enemies:
                enemy.freeze()
            return True
        return False       


class NeoBeam:
    """
    弾幕に関するクラス
    """
    def __init__(self, bird:Bird, num:int):
        self.bird = bird
        self.num = num

    def gen_beams(self):
        """
        それぞれのビームの角度を計算しタプルで返す
        """
        beams = []
        for angle in range(-50, +51, int(100/(self.num-1))):
            beam = Beam(self.bird, angle)
            beams.append(beam)
        return beams


class Score:
    """
    スコアの計算に関するクラス
    """
    def __init__(self):
        """
        撃ち落とした敵などの数を計算し表示するクラス
        """
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.lv = 1
        self.next_exp = 10 # 次のレベルまでの経験値
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 150, HEIGHT-50

    def gain_exp(self, exp: int):
        """
        スコアに経験値を加算し，レベルアップの判定を行う
        引数 exp：加算する経験値
        """
        self.value += exp
        if self.value >= self.next_exp:
            self.lv += 1
            self.next_exp += int(self.lv * 10)  # 次のレベルアップまでの経験値を増加

    def update(self, screen:pg.Surface):
        self.image = self.font.render(f"Score: {self.value}  Level:{self.lv}", 0, self.color)
        screen.blit(self.image, self.rect)


def GameOver(screen:pg.Surface):
    """
    gameoverに関する関数
    """
    fin_img = pg.Surface((WIDTH, HEIGHT))
    pg.draw.rect(fin_img, (0, 0, 0), (0, 0, WIDTH, HEIGHT), 0)
    fin_img.set_alpha(128)
    
    fonto1 = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 100)
    txt1 = fonto1.render("GAME OVER", True, (255, 255, 255))
    fonto2 = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 80)
    txt2 = fonto2.render(f"Score:{save_score}  Level:{save_lv}", True, (255, 255, 255))
    fonto3 = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 50)
    txt3 = fonto3.render("PRESS SPACE TO RESTART", True, (255, 255, 255))

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                main(screen)
                GameOver(screen)
                return 0
            
        screen.blit(fin_img, [0, 0])
        screen.blit(txt1, [325, 200])
        screen.blit(txt2, [240, 400])
        screen.blit(txt3, [300, 500])
        pg.display.update()


class BirdHpUI:
    """
    こうかとんのHPのUIに関するクラス
    """
    def __init__(self, bird:Bird):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (255, 0, 0)
        self.value = bird.hp
        self.image = self.font.render(f"残りHP: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1000, HEIGHT-50

    def update(self, screen:pg.Surface, bird:Bird):
        self.value = bird.hp
        self.image = self.font.render(f"残りHP: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)



class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: Enemy, life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()

class Weapon:
    """1種類の武器情報を保持するクラス"""
    
    def __init__(
        self,
        name:str,
        cooldown:float,
        fire_func: Callable[[Bird], List[pg.sprite.Sprite]], # 発射関数
    ) -> None: 
        self.name = name 
        self.cooldown = cooldown
        self._fire_func = fire_func 
        self._last_fire_time = 0.0
        
    def _ready(self) -> bool: # クールダウン経過判定
        """クールダウン経過判定"""
        return time.time() - self._last_fire_time >= self.cooldown # クールダウン時間を超えたかどうか
    
    def fire(self, bird: Bird) -> List[pg.sprite.Sprite]: # 発射処理
        """武器を発射し、生成された弾Spriteを返す"""
        if not self._ready(): 
            return[] # クールダウン中は何もしない
        self._last_fire_time = time.time() # 最後の発射時間を更新
        return self._fire_func(bird) # 発射関数を呼び出して弾を生成 


class WeaponSystem: 
    """複数武器を切替・発射するマネージャー。"""
    
    def __init__(self, player: Bird) -> None: # 武器システムの初期化
        self._player = player # 武器を発射するプレイヤー
        self._weapons: list[Weapon] = [] # 武器のリスト
        self._idx = 0  # 現在の武器のインデックス
        
    def add(self, weapon) -> None:
        self._weapons.append(weapon) # 武器を追加
        
    def next(self) -> None:
        """次の武器に切り替える"""
        if self._weapons: # 武器が存在する場合
            self._idx = (self._idx + 1) % len(self._weapons) # 循環する
            
    @property # 現在の武器を取得
    def current(self) -> Weapon: # 現在の武器を返す
        return self._weapons[self._idx] 
    
    def fire(self) -> List[pg.sprite.Sprite]: # 現在の武器を発射
        return self.current.fire(self._player)


def main(screen:pg.Surface):
    pg.init()
    bg_img = pg.image.load(f"fig/stage.png") 
    
    score  = Score()
    beams = pg.sprite.Group()
    enemies = pg.sprite.Group()  # 敵管理用グループ
    exps = pg.sprite.Group()
    bird = Bird(3, (900, 400))
    b_hp_ui = BirdHpUI(bird)
    # 武器システム設定
    weapon_system = WeaponSystem(bird)
    weapon_system.add(Weapon("Beam", 0.15, lambda b: [Beam(b)])) # 通常のビームを放つ
    weapon_system.add(Weapon("Spread", 0.8, lambda b: NeoBeam(b, 3+int(score.lv//5)).gen_beams())) # 3+lvの数でビームを放つ
    special_shot_manager = SpecialShot() # SpecialShotインスタンスを作成


    clock = pg.time.Clock()

    tmr = 0
    pg.mixer.init()
    pg.mixer.music.load("bgm/maou_game_dangeon19.mp3") #bgmの設定
    pg.mixer.music.play(-1)
    sound_effect = pg.mixer.Sound("bgm/8bit_shoot2.mp3") #効果音の設定
    sound_effect.set_volume(0.7)

    while True:
        key_lst = pg.key.get_pressed() 
        for event in pg.event.get(): 
            if event.type == pg.QUIT: # ウィンドウの×ボタンで終了
                return 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_TAB: # TABキーで武器を切り替え
                    weapon_system.next()
                elif event.key == pg.K_SPACE: # スペースキーで武器を発射
                    sound_effect.play()
                    beams.add(weapon_system.fire())
                elif event.key == pg.K_e: # 'e'キーでスペシャルショット発動
                    sound_effect.play()
                    special_shot_manager.activate(bird, score, enemies, beams)


        # 1秒ごとに敵を出現
        if tmr % 60 == 0:
            for _ in range(min(1 + tmr // 600, 10)):
                enemies.add(Enemy(bird, tmr))
        
        # 現在武器名を表示
        font = pg.font.Font(None, 36) # フォントの設定
        hud = font.render(f"Weapon: {weapon_system.current.name}", True, (255, 255, 255)) # 武器名を描画
        screen.blit(hud, (10, 10)) # 画面左上に表示
        
        pg.display.update()
        # ゲームオーバー判定
        if pg.sprite.spritecollide(bird, enemies, True):
            if bird.hp > 1:
                bird.hp -= 1
            elif bird.hp == 1:
                print("Game Over!")
                time.sleep(1)
                return 0
                
        for emy in pg.sprite.groupcollide(enemies, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            score.gain_exp(5)
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        screen.blit(bg_img, [0, 0])
        bird.update(key_lst, screen)
        score.update(screen)
        b_hp_ui.update(screen, bird)
        
        beams.update()
        beams.draw(screen)
        enemies.update()
        enemies.draw(screen)    
        
        tmr += 1
        clock.tick(50)
        exps.update()
        exps.draw(screen)
        
        global save_score, save_lv
        save_score = score.value
        save_lv = score.lv


if __name__ == "__main__":
    pg.init()
    menu()
    pg.quit()
    sys.exit()