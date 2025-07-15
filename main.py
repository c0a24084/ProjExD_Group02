import os
import random
import sys
import time
import pygame as pg

# --- 定数 ---
WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数

# スクリプトの実行ディレクトリに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))


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


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0) # こうかとんの向きを表すタプルを定義

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

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
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            if tuple(sum_mv) in __class__.imgs:
                self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv) # 合計移動量sum_mvが[0,0]でない時，self.direをsum_mvの値で更新
        screen.blit(self.img, self.rct)

class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    DIRE_DATA = {
        # こうかとんが右向き (+5, 0)
        (+5, 0): {
            "center": ((+1, 0), 0),   # 0度
            "left":   ((+0.8, -0.8), 30), 
            "right":  ((+0.8, +0.8), -30), 
        },
        # こうかとんが左向き 
        (-5, 0): {
            "center": ((-1, 0), 180), 
            "left":   ((-0.8, +0.8), -150), 
            "right":  ((-0.8, -0.8), 150), 
        },
        # こうかとんが上向き 
        (0, -5): {
            "center": ((0, -1), 90), 
            "left":   ((+0.5, -0.8), 60),   
            "right":  ((-0.5, -0.8), 120), 
        },
        # こうかとんが下向き 
        (0, +5): {
            "center": ((0, +1), -90), 
            "left":   ((-0.5, +0.8), -120), 
            "right":  ((+0.5, +0.8), -60), 
        },
        # 以下、斜め方向 
        (+5, -5): { # 右上
            "center": ((0.707, -0.707), 45),
            "left":   ((0.966, -0.259), 15), 
            "right":  ((0.259, -0.966), 75), 
        },
        (-5, -5): { # 左上
            "center": ((-0.707, -0.707), 135),
            "left":   ((-0.259, -0.966), 105), 
            "right":  ((-0.966, -0.259), 165),
        },
        (-5, +5): { # 左下
            "center": ((-0.707, 0.707), -135),
            "left":   ((-0.966, 0.259), -165),
            "right":  ((-0.259, 0.966), -105), 
        },
        (+5, +5): { # 右下
            "center": ((0.707, 0.707), -45),
            "left":   ((0.259, 0.966), -75), 
            "right":  ((0.966, 0.259), -15), 
        },
    }

    def __init__(self, bird:"Bird", beam_type: str = "center", size:float = 1.0, is_special:bool = False):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        引数 beam_type：ビームの種類 ("center", "left", "right")
        引数 size:ビームのサイズを追加
        引数 is_special: 特殊ビームかどうかを判定する真偽値
        """
        # こうかとんの基本の向きを取得
        base_dire = bird.dire
        if base_dire not in Beam.DIRE_DATA:
            base_dire = (+5, 0) # デフォルトを右向きにする

        dire_info = Beam.DIRE_DATA.get(base_dire, Beam.DIRE_DATA[(+5, 0)])[beam_type]
        self.vx, self.vy = dire_info[0] # 速度の係数
        angle = dire_info[1] # 回転角度

        # 画像をロードし、指定された角度で回転
        self.img = pg.transform.rotozoom(pg.image.load("fig/beam.png"), angle, size)
        
        self.rct = self.img.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx / 2 # 調整
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy / 2 # 調整
        self.is_special = is_special
        
    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            # 速度ベクトルの大きさを調整 
            self.rct.move_ip(self.vx*10, self.vy*10)
            screen.blit(self.img, self.rct)
            return self # 画面内にいる場合は自身を返す
        else:
            return None # 画面外に出たらNoneを返す
        
class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5
        self.is_frozen = False  
        self.freeze_timer = 0   

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if not self.is_frozen:
            yoko, tate = check_bound(self.rct)
            if not yoko:
                self.vx *= -1
            if not tate:
                self.vy *= -1
            self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct) # 凍結中でも描画は行うように変更

    def freeze(self): 
        """爆弾を凍結状態にする"""
        self.is_frozen = True   
        self.freeze_timer = 3 * 50 # 3秒 * 50fps = 150フレーム 
    
    def unfreeze(self): 
        """爆弾の凍結状態を解除する"""
        self.is_frozen = False 
        self.freeze_timer = 0 

class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, obj_rct: pg.Rect):
        """
        爆発エフェクトの画像Surfaceを生成する
        引数 obj_rct：爆発するオブジェクトのRect
        """
        original_img = pg.image.load("fig/explosion.gif")
        self.imgs = [original_img, pg.transform.flip(original_img, True, True)]
        self.img_idx = 0
        self.img = self.imgs[self.img_idx]
        self.rct = self.img.get_rect(center=obj_rct.center)
        self.life = 20

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを表示する
        引数 screen：画面Surface
        """
        if self.life > 0:
            self.img = self.imgs[self.img_idx % 2]
            screen.blit(self.img, self.rct)
            self.img_idx += 1
            self.life -= 1
            return self
        else:
            return None

class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        """
        スコア表示の初期設定を行うイニシャライザ
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.value = 0
        self.img = self.fonto.render(f"Score: {self.value}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.bottomleft = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface):
        """
        現在のスコアを表示させる文字列Surfaceを生成し、スクリーンにblitする
        引数 screen：画面Surface
        """
        self.img = self.fonto.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.img, self.rct)

class SpecialShot:
    """
    必殺技に関するクラス
    """
    EXP = 100 # 特殊ビーム発射に必要なスコア
    FREEZE_DURATION_FRAMES = 3 * 50 # 凍結時間（フレーム数）

    def __init__(self):
        """
        SpecialShotの初期設定を行う (scoreはactivate時に渡す)
        """
        pass # 現状では特別な初期化は不要

    def create_beam_and_freeze_bombs(self, bird: "Bird", score: "Score", bombs: list["Bomb"], beams: list["Beam"]) -> bool:
        """
        特殊ビームを発射し、爆弾を凍結させる処理を行う。
        発動に成功したらTrue、失敗したらFalseを返す。
        引数 bird: こうかとんインスタンス
        引数 score: スコアインスタンス
        引数 bombs: 爆弾のリスト
        引数 beams: ビームのリスト
        """
        if score.value >= SpecialShot.EXP:
            beams.append(Beam(bird, "center", 3.0, True)) # 特大ビームを発射 (is_special=True)
            score.value -= SpecialShot.EXP # スコアを消費

            # 全ての爆弾を一定時間停止させる
            for bomb in bombs:
                if bomb is not None:
                    bomb.freeze()
            return True
        return False

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams = []  # 複数のビームを管理するための空のリスト

    explosions = []
    score = Score()
    special_shot_manager = SpecialShot() # SpecialShotインスタンスを作成
    
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.append(Beam(bird)) # 通常ビームは"center"タイプで発射
                if event.key == pg.K_LSHIFT: # シフトキーが押されたら
                    # こうかとんの向きに応じて、3本のビームを発射
                    beams.append(Beam(bird, "left")) 
                    beams.append(Beam(bird, "center"))    
                    beams.append(Beam(bird, "right"))
                if event.key == pg.K_e: # 'e'キーで特大ビーム
                    # ここにSpecialShotクラスのロジックを呼び出す
                    special_shot_manager.create_beam_and_freeze_bombs(bird, score, bombs, beams)
        
        screen.blit(bg_img, [0, 0])
        
        # こうかとんと爆弾の衝突判定
        for bomb in bombs:
            if bomb is not None and bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return
        
        # 爆弾とビームの衝突判定ループ
        for i, bomb in enumerate(bombs):
            if bomb is None:
                continue
            for j, beam in enumerate(beams):
                if beam is None:
                    continue
                if beam.rct.colliderect(bomb.rct):
                    explosions.append(Explosion(bomb.rct))
                    bombs[i] = None # 爆弾は消える
                    bird.change_img(6, screen) # こうかとんの画像を一時的に変更
                    score.value += 1 # スコア加算
                    
                    if not beam.is_special: # 特殊ビームでなければビームを消す
                        beams[j] = None
                    # 特殊ビームの場合は、ビームは消えない (衝突しても消えない)
                    if bombs[i] is None: # 爆弾が消えたら、この爆弾に対するビームのループは抜ける
                        break 

        beams = [beam for beam in beams if beam is not None]
        bombs = [bomb for bomb in bombs if bomb is not None]
        explosions = [exp for exp in explosions if exp is not None]

        # 各オブジェクトの更新と描画
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        for beam in beams:
            beam_result = beam.update(screen)
            if beam_result is None:
                beams.remove(beam) # 画面外に出たビームをリストから除去

        for bomb in bombs:
            bomb.update(screen)
            # 凍結タイマーの更新と解除
            if bomb.is_frozen:
                bomb.freeze_timer -= 1
                if bomb.freeze_timer <= 0:
                    bomb.unfreeze()

        for exp in explosions:
            exp_result = exp.update(screen)
            if exp_result is None:
                explosions.remove(exp) # 表示期間が終わった爆発エフェクトをリストから除去

        score.update(screen) # スコア表示の更新
        pg.display.update() # 画面の更新
        tmr += 1 # 経過フレーム数を更新
        clock.tick(50) 

# --- プログラム実行 ---
if __name__ == "__main__":  
    pg.init()   # Pygameの初期化
    main()      # ゲームの実行
    pg.quit()   # Pygameの終了
    sys.exit()  # プログラムの終了