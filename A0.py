import datetime
import requests 
import sys
import cv2
import time
import logging
from JoycontrolPlugin import JoycontrolPlugin

logger = logging.getLogger(__name__)

class A0(JoycontrolPlugin):
    def __init__(self, controller_state, options):
        super().__init__(controller_state, options)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.cap.set(cv2.CAP_PROP_FPS, 10)
        # スクリプト実行時に渡される引数からポケモンのデータを取得
        pokemons_data = self.data()
        if len(sys.argv) > 1 and sys.argv[5] in pokemons_data:
            self.pokemon = sys.argv[5]
            self.pokemon_data = pokemons_data[sys.argv[5]]
            logger.info(f"ポケモン: {self.pokemon}")
            logger.info(f"上昇補正HP: {self.pokemon_data['up']}")
            logger.info(f"無補正HP: {self.pokemon_data['normal']}")
            logger.info(f"下降補正HP: {self.pokemon_data['low']}")
        else:
            logger.error("指定されたポケモンのデータが見つかりません。")
            sys.exit(1)

    def matching_rate(self, frame, img, gray=True):
        if gray:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(frame, img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        print(f"Max Val: {max_val} Max Loc: {max_loc}")
        return max_val

    def get_frame(self):
        for _ in range(2):
            ret, frame = self.cap.read()
        return frame
    
    def notify(self):
        headers = {
            'Content-type': 'application/json',
        }
        json_data = {
            'text': f"A0 {self.pokemon}を見つけました。",
        }
        response = requests.post(
            # slack channel のURL
            headers=headers,
            json=json_data,
        )
    def data(self):
        data = {
          'ラティアス': {'up': 380, 'normal': 369, 'low': 357},
          'フリーザー': {'up': 388, 'normal': 376, 'low': 363},
          'ライコウ': {'up': 388, 'normal': 376, 'low': 363},
          'ラティオス': {'up': 396, 'normal': 383, 'low': 369},
          'ルギア': {'up': 396, 'normal': 383, 'low': 369},
          'サンダー': {'up': 396, 'normal': 383, 'low': 369},
          'カイオーガ': {'up': 411, 'normal': 397, 'low': 382},
          'ファイヤー': {'up': 411, 'normal': 397, 'low': 382},
          'ルナアーラ': {'up': 431, 'normal': 415, 'low': 398},
          'レイスポス': {'up': 483, 'normal': 474, 'low': 464},
          'イーユイ': {'up': 489, 'normal': 479, 'low': 468},
          'チオンジェン': {'up': 495, 'normal': 485, 'low': 474},
          'マシマシラ': {'up': 499, 'normal': 488, 'low': 477},
          'スイクン': {'up': 499, 'normal': 488, 'low': 477},
          'ガチグマ(あかつき)': {'up': 0, 'normal': 481, 'low': 0},
          'ネクロズマ': {'up': 0, 'normal': 0, 'low': 0},
          'レシラム': {'up': 0, 'normal': 0, 'low': 0},
          'モモワロウ': {'up': 420, 'normal': 411, 'low': 395}
        }
        return data

    async def run(self):
        # ベースパスを設定（A0ディレクトリの親ディレクトリまで）
        base_path = "/home/ubuntu/joycontrol-pluginloader/plugins/custom/sorce/"

        fight = cv2.imread(base_path + "iyui/fight.png")

        # pokemon_data 辞書の値を使用して画像を読み込む
        h_up = cv2.imread(base_path + "A0/" + str(self.pokemon_data['up']) + ".png")
        h_normal = cv2.imread(base_path + "A0/" + str(self.pokemon_data['normal']) + ".png")
        h_low = cv2.imread(base_path + "A0/" + str(self.pokemon_data['low']) + ".png")

        state = 'restart'

        try:
            while True:
                start_time = time.time()
                frame = self.get_frame()
                print(f"{state}")

                if state == 'start':
                    if self.matching_rate(self.get_frame()[700:780,1500:1800], fight) > .90:
                        state = 'buttle'
                    else:
                        await self.wait(2.0)
                        if self.matching_rate(self.get_frame()[700:780,1500:1800], fight) > .90:
                            state = 'buttle'
                        else:
                            await self.button_push('a')
                elif state == 'buttle':
                    await self.button_push('a')
                    await self.wait(0.5)
                    await self.button_push('a')
                    await self.wait(0.5)
                    await self.button_push('a')
                    await self.wait(9.0)

                    # フレームを保存するためのバッファ
                    frame_buffer = []
                    buffer_size = 10  # バッファサイズ
                    count = 0
                    while count < buffer_size:
                        frame = self.get_frame()
                        frame_buffer.append(frame)
                        count += 1

                    count = 0
                    for frame in frame_buffer:
                        frame = frame[1000:1040,200:280] 
                        count += 1
                        state = 'restart'
                        cv2.imwrite(f"{count}.png", frame)
                        if (self.matching_rate(frame, h_up) > .90) or (self.matching_rate(frame, h_normal) > .90) or (self.matching_rate(frame, h_low) > .90):
                            state = 'find_a0'
                            break
                elif state == 'find_a0':
                    self.notify()
                    sys.exit()
                elif state == 'restart':
                    await self.button_push('home')
                    await self.wait(1.0)
                    await self.button_push('x')
                    await self.wait(0.5)
                    await self.button_push('a')
                    await self.wait(5.0)

                    await self.button_push('a')
                    await self.wait(2.0)
                    await self.button_push('a')
                    state = 'start'


                elapsed_time = time.time() - start_time
                sleep_time = max(1/self.fps - elapsed_time, 0)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.stop_recording()
