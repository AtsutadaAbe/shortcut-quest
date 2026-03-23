import tkinter as tk
import json
import os
import sys
import math
import time
import random
import winsound

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_questions():
    path = resource_path("questions.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Shortcut Quest")
        self.root.geometry("560x700")

        self.questions = load_questions()

        self.normal_questions = [q for q in self.questions if q.get("type") == "normal"]
        self.boss_questions = [q for q in self.questions if q.get("type") == "boss"]

        if len(self.normal_questions) < 1:
            raise ValueError("questions.json に normal 問題が1問以上必要です。")

        if len(self.boss_questions) < 5:
            raise ValueError("questions.json に boss 問題が5問以上必要です。")

        self.stage_number = 0           # 0～8: 通常戦, 9: ボス戦
        self.enemy_hp = 1
        self.enemy_max_hp = 1
        self.is_boss = False
        self.waiting_for_next = False
        self.game_started = False

        self.start_time = None
        self.clear_time = None

        self.current_question = None
        self.current_boss_questions = []
        self.boss_question_index = 0

        self.previous_normal_question = None

        self.slime_images = [
            self.load_image_fit("assets/slime_blue.png", 260, 180),
            self.load_image_fit("assets/slime_green.png", 260, 180),
            self.load_image_fit("assets/slime_orange.png", 260, 180),
            self.load_image_fit("assets/slime_pink.png", 260, 180),
            self.load_image_fit("assets/slime_yellow.png", 260, 180),
        ]

        self.previous_slime_image = None

        # 読み込み失敗（None）を除外
        self.slime_images = [img for img in self.slime_images if img is not None]

        if not self.slime_images:
            raise ValueError("スライム画像が読み込めません。assetsフォルダを確認してください。")
        
        self.slime_image = self.load_image_fit("assets/slime.png", 260, 180)
        self.boss_image = self.load_image_fit("assets/boss.png", 260, 180)

        self.title_label = tk.Label(root, text="", font=("Meiryo", 24, "bold"))
        self.title_label.pack(pady=(20, 10))

        self.description_label = tk.Label(root, text="", font=("Meiryo", 13), justify="center")
        self.description_label.pack(pady=(5, 15))

        self.start_button = tk.Button(
            root,
            text="ゲームスタート",
            font=("Meiryo", 14, "bold"),
            width=18,
            command=self.start_game
        )
        self.start_button.pack(pady=(10, 20))

        self.enemy_image_label = tk.Label(root, text="")
        self.enemy_image_label.pack(pady=(5, 5))

        self.enemy_label = tk.Label(root, text="", font=("Meiryo", 16, "bold"))
        self.enemy_label.pack(pady=(2, 2))

        self.hp_bar_label = tk.Label(root, text="", font=("Consolas", 14))
        self.hp_bar_label.pack(pady=(0, 5))

        self.message_label = tk.Label(root, text="", font=("Meiryo", 12), fg="purple")
        self.message_label.pack(pady=2)

        self.question_label = tk.Label(root, text="", font=("Meiryo", 20, "bold"), wraplength=500)
        self.question_label.pack(pady=10)

        self.input_label = tk.Label(root, text="", font=("Meiryo", 16))
        self.input_label.pack(pady=3)

        self.result_label = tk.Label(root, text="", font=("Meiryo", 18, "bold"))
        self.result_label.pack(pady=5)

        self.answer_label = tk.Label(root, text="", font=("Meiryo", 12), fg="gray")
        self.answer_label.pack(pady=1)

        self.time_label = tk.Label(root, text="", font=("Meiryo", 14), fg="darkgreen")
        self.time_label.pack(pady=6)

        self.rank_label = tk.Label(root, text="", font=("Meiryo", 16, "bold"), fg="darkorange")
        self.rank_label.pack(pady=6)

        self.retry_button = tk.Button(
            root,
            text="もう一度ゲームをする",
            font=("Meiryo", 13, "bold"),
            width=18,
            command=self.return_to_start_screen
        )

        self.root.bind_all("<KeyPress>", self.on_key_press)
        self.root.after(100, self.set_focus)

        self.show_start_screen()

    def set_focus(self):
        self.root.focus_force()

    def hide_all_widgets(self):
        self.title_label.pack_forget()
        self.description_label.pack_forget()
        self.start_button.pack_forget()

        self.enemy_image_label.pack_forget()
        self.enemy_label.pack_forget()
        self.hp_bar_label.pack_forget()
        self.message_label.pack_forget()
        self.question_label.pack_forget()
        self.input_label.pack_forget()
        self.result_label.pack_forget()
        self.answer_label.pack_forget()

        self.time_label.pack_forget()
        self.rank_label.pack_forget()
        self.retry_button.pack_forget()

    def load_image_fit(self, path, max_width, max_height):
        full_path = resource_path(path)

        if not os.path.exists(full_path):
            return None

        try:
            image = tk.PhotoImage(file=full_path)
        except Exception:
            return None

        width = image.width()
        height = image.height()

        if width <= max_width and height <= max_height:
            return image

        scale_w = math.ceil(width / max_width)
        scale_h = math.ceil(height / max_height)
        scale = max(scale_w, scale_h)

        return image.subsample(scale, scale)

    def show_start_screen(self):
        self.hide_all_widgets()

        self.title_label.pack(pady=(40, 18))
        self.description_label.pack(pady=(10, 28))
        self.start_button.pack(pady=(12, 30))
        self.message_label.pack(pady=18)

        self.title_label.config(text="Shortcut Quest")
        self.description_label.config(
            text=(
                "Excelショートカットで敵を倒そう！\n\n"
                "・通常戦 9問（1匹につき1問）\n"
                "・ボス戦 1回（5問連続）\n"
                "・問題はランダム表示\n"
                "・正解で敵にダメージ\n"
                "・ボスを倒したらクリア\n"
                "・クリアタイムも計測されます"
            )
        )
        self.message_label.config(text="スタートボタンを押してください")

    def start_game(self):
        self.hide_all_widgets()

        self.game_started = True
        self.stage_number = 0
        self.waiting_for_next = False
        self.start_time = time.time()
        self.clear_time = None
        self.current_question = None
        self.current_boss_questions = []
        self.boss_question_index = 0
        self.previous_normal_question = None

        self.enemy_image_label.pack(pady=(40, 10))
        self.enemy_label.pack(pady=(5, 4))
        self.hp_bar_label.pack(pady=(0, 10))
        self.message_label.pack(pady=4)
        self.question_label.pack(pady=30)
        self.input_label.pack(pady=8)
        self.result_label.pack(pady=8)
        self.answer_label.pack(pady=3)

        self.setup_battle()
        self.show_question()
        self.set_focus()

    def setup_battle(self):
        self.is_boss = (self.stage_number == 9)

        if self.is_boss:
            self.enemy_max_hp = 5
            self.enemy_hp = 5
            self.message_label.config(text="🔥 ボス出現！ 🔥")
            self.show_enemy_image(self.boss_image, fallback_text="[BOSS IMAGE]")

            self.current_boss_questions = random.sample(self.boss_questions, 5)
            self.boss_question_index = 0
            self.current_question = self.current_boss_questions[self.boss_question_index]

        else:
            self.enemy_max_hp = 1
            self.enemy_hp = 1
            self.message_label.config(text="敵出現！")

            available_slimes = [
                img for img in self.slime_images
                if img != getattr(self, "previous_slime_image", None)
            ]

            if not available_slimes:
                available_slimes = self.slime_images

            slime_image = random.choice(available_slimes)
            self.previous_slime_image = slime_image
            self.show_enemy_image(slime_image, fallback_text="[SLIME IMAGE]")

            available_questions = [
                q for q in self.normal_questions
                if q != self.previous_normal_question
            ]

            if not available_questions:
                available_questions = self.normal_questions

            self.current_question = random.choice(available_questions)
            self.previous_normal_question = self.current_question

        self.update_enemy_label()
        self.root.after(1000, self.clear_message)

    def clear_message(self):
        if not self.is_boss:
            self.message_label.config(text="")

    def show_enemy_image(self, image, fallback_text=""):
        if image:
            self.enemy_image_label.config(image=image, text="")
            self.enemy_image_label.image = image
        else:
            self.enemy_image_label.config(image="", text=fallback_text, font=("Meiryo", 16))
            self.enemy_image_label.image = None

    def update_enemy_label(self):
        enemy_name = "ボス" if self.is_boss else "スライム"
        self.enemy_label.config(text=f"敵：{enemy_name}   HP: {self.enemy_hp}/{self.enemy_max_hp}")

        bar = "■" * self.enemy_hp + "□" * (self.enemy_max_hp - self.enemy_hp)
        self.hp_bar_label.config(text=f"HPバー: {bar}")

    def show_question(self):
        q = self.current_question["question"]
        self.question_label.config(text=q)
        self.input_label.config(text="入力: まだありません")
        self.result_label.config(text="")
        self.answer_label.config(text="")

    def on_key_press(self, event):
        if not self.game_started:
            return

        if self.waiting_for_next:
            return

        pressed_text = self.get_pressed_shortcut(event)

        # Ctrl単体など、まだ判定しないキーは無視する
        if pressed_text is None:
            return

        self.input_label.config(text=f"入力: {pressed_text}")

        correct_answer = self.current_question["answer"]

        if pressed_text == correct_answer:
            self.handle_correct(correct_answer)
        else:
            self.handle_incorrect(correct_answer)

    def handle_correct(self, correct_answer):

        winsound.Beep(1200, 120)

        self.enemy_hp -= 1
        self.update_enemy_label()

        self.result_label.config(text="正解！", fg="blue")
        self.answer_label.config(text="")

        if self.is_boss:
            self.waiting_for_next = True

            if self.enemy_hp <= 0:
                self.show_defeat_effect("👑 ボス撃破！ 👑", color="darkred")
                self.message_label.config(text="ゲームクリア！")
                self.root.after(1200, self.show_clear_screen)
            else:
                self.result_label.config(text="⚔ ボスにダメージ！ ⚔", fg="blue")
                self.message_label.config(text="次のボス問題へ進みます...")
                self.root.after(900, self.next_question)

        else:
            if self.enemy_hp <= 0:
                self.waiting_for_next = True
                self.show_defeat_effect("💥 スライム撃破！ 💥", color="red")
                self.message_label.config(text="次の問題へ進みます...")
                self.root.after(1000, self.next_question)

    def handle_incorrect(self, correct_answer):

        winsound.Beep(400, 200)

        self.result_label.config(text="不正解", fg="red")
        self.answer_label.config(text=f"答え: {correct_answer}")
    
    def show_defeat_effect(self, message, color="red"):
        self.result_label.config(text=message, fg=color)
        self.answer_label.config(text="")
        self.enemy_image_label.config(image="", text="")

    def next_question(self):
        self.waiting_for_next = False

        if self.is_boss:
            self.boss_question_index += 1

            if self.boss_question_index >= 5:
                self.show_clear_screen()
                return

            self.current_question = self.current_boss_questions[self.boss_question_index]
            self.update_enemy_label()
            self.message_label.config(text="ボス戦 継続中！")
            self.show_question()
        else:
            self.stage_number += 1

            if self.stage_number >= 10:
                self.show_clear_screen()
                return

            self.setup_battle()
            self.show_question()

    def format_time(self, seconds):
        total_seconds = int(seconds)
        minutes = total_seconds // 60
        remain_seconds = total_seconds % 60
        return f"{minutes}分 {remain_seconds}秒"
    
    def get_rank(self, seconds):
        if seconds < 40:
            return "ランク：勇者\nあなたは勇者です！"
        elif seconds < 60:
            return "ランク：剣士\nあなたは剣士です！"
        elif seconds < 90:
            return "ランク：冒険者\nあなたは冒険者です！"
        else:
            return "ランク：旅人\nあなたは旅人です！"

    def show_clear_screen(self):
        self.hide_all_widgets()

        self.game_started = False
        self.clear_time = time.time() - self.start_time

        self.message_label.pack(pady=(70, 12))
        self.title_label.pack(pady=(12, 28))
        self.result_label.pack(pady=20)
        self.time_label.pack(pady=14)
        self.rank_label.pack(pady=14)
        self.retry_button.pack(pady=24)

        self.message_label.config(text="Shortcut Quest MVP 完了")
        self.title_label.config(text="ゲームクリア！", font=("Meiryo", 26, "bold"))
        self.result_label.config(text="10戦クリアおめでとう！", fg="blue", font=("Meiryo", 18, "bold"))
        self.time_label.config(text=f"クリアタイム: {self.format_time(self.clear_time)}")

        rank_text = self.get_rank(self.clear_time)
        self.rank_label.config(text=rank_text)

    def return_to_start_screen(self):
        self.stage_number = 0
        self.enemy_hp = 1
        self.enemy_max_hp = 1
        self.is_boss = False
        self.waiting_for_next = False
        self.game_started = False
        self.start_time = None
        self.clear_time = None
        self.current_question = None
        self.current_boss_questions = []
        self.boss_question_index = 0

        self.previous_normal_question = None

        self.show_start_screen()
        self.set_focus()

    def get_pressed_shortcut(self, event):
        ctrl_pressed = bool(event.state & 0x4)
        key = event.keysym.lower()

        # 修飾キー単体は判定しない
        ignore_keys = {
            "control_l", "control_r",
            "shift_l", "shift_r",
            "alt_l", "alt_r",
            "super_l", "super_r"
        }

        if key in ignore_keys:
            return None

        # Ctrl + アルファベット はまとめて Ctrl+○ の形で返す
        if ctrl_pressed and len(key) == 1 and key.isalpha():
            return f"Ctrl+{key.upper()}"

        # それ以外はそのまま返す
        return key

root = tk.Tk()
game = Game(root)
root.mainloop()