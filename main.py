import os
import random
import json
from io import BytesIO

from PIL import Image as ImageW
from PIL import ImageDraw, ImageFont

from astrbot.api.all import *  # noqa: F403
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star, register

try:
    os.system("pip install pyspellchecker")
    logger.log("Wordle已尝试安装pyspellchecker库")
except:
    logger.warning("Wordle未自动安装pyspellchecker库")
    logger.warning("这可能导致拼写检查的失败，请手动在AstrBot目录中requirements.txt添加一行“pyspellchecker”")

from spellchecker import SpellChecker

class WordleGame:
    def __init__(self, answer: str):
        self.answer = answer.upper()
        self.length = len(answer)
        self.max_attempts = self.length + 1
        self.guesses: list[str] = []
        self.feedbacks: list[list[int]] = []

        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
        self.font_file = os.path.join(self.plugin_dir, "MinecraftAE.ttf")   # 这里可以修改字体为自定义字体

        self._font = ImageFont.truetype(self.font_file, 40)  #设定字体、字号、字重

    async def gen_image(self) -> bytes:
        CELL_COLORS = {
            2: (106, 170, 100),
            1: (201, 180, 88),
            0: (120, 124, 126),
            -1: (211, 214, 218),
        }
        BACKGROUND_COLOR = (255, 255, 255)
        TEXT_COLOR = (255, 255, 255)

        CELL_SIZE = 60
        CELL_MARGIN = 5
        GRID_MARGIN = 5

        cell_stride = CELL_SIZE + CELL_MARGIN
        width = GRID_MARGIN * 2 + cell_stride * self.length - CELL_MARGIN
        height = GRID_MARGIN * 2 + cell_stride * self.max_attempts - CELL_MARGIN

        image = ImageW.new("RGB", (width, height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        for row in range(self.max_attempts):
            y = GRID_MARGIN + row * cell_stride

            for col in range(self.length):
                x = GRID_MARGIN + col * cell_stride

                if row < len(self.guesses) and col < len(self.guesses[row]):
                    letter = self.guesses[row][col].upper()
                    feedback_value = self.feedbacks[row][col]
                    cell_color = CELL_COLORS[feedback_value]
                else:
                    letter = ""
                    cell_color = CELL_COLORS[-1]

                draw.rectangle(
                    [x, y, x + CELL_SIZE, y + CELL_SIZE], fill=cell_color, outline=None
                )

                if letter:
                    text_bbox = draw.textbbox((0, 0), letter, font=self._font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                    letter_x = x + (CELL_SIZE - text_width) // 2 + 2
                    letter_y = y + (CELL_SIZE - text_height) // 2 + 1

                    draw.text((letter_x, letter_y), letter, fill=TEXT_COLOR, font=self._font)

        with BytesIO() as output:
            image.save(output, format="PNG")
            return output.getvalue()

    async def guess(self, word: str) -> bytes:
        word = word.upper()
        self.guesses.append(word)

        feedback = [0] * self.length
        answer_char_counts: dict[str, int] = {}
        
        for i in range(self.length):
            if word[i] == self.answer[i]:
                feedback[i] = 2
            else:
                answer_char_counts[self.answer[i]] = answer_char_counts.get(self.answer[i], 0) + 1
        
        for i in range(self.length):
            if feedback[i] != 2:
                char = word[i]
                if char in answer_char_counts and answer_char_counts[char] > 0:
                    feedback[i] = 1
                    answer_char_counts[char] -= 1
        
        self.feedbacks.append(feedback)
        result = await self.gen_image()

        return result
    
    @property
    def is_game_over(self):
        if not self.guesses:
            return False
        return len(self.guesses) >= self.max_attempts

    @property
    def is_won(self):
        return self.guesses and self.guesses[-1].upper() == self.answer


@register(
    "astrbot_plugin_wordle",
    "Raven95676",
    "Astrbot wordle游戏，支持指定位数",
    "1.0.0",
    "https://github.com/Raven95676/astrbot_plugin_wordle",
)
class PluginWordle(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.game_sessions: dict[str, WordleGame] = {}

    @staticmethod
    async def get_answer(length):
        try:
            wordlist_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "wordlist"
            )

            if not os.path.exists(wordlist_path):
                logger.error("词表文件不存在")
                return None

            # 获取单词文件
            word_file_list = os.listdir(wordlist_path)
            global word_dict
            word_dict = {}
            # 遍历单词表，并用字典接收内容
            for word_file in word_file_list:
                with open(os.path.join(wordlist_path,word_file),"r",encoding="utf-8") as f:
                    word_dict.update(json.load(f)) 
                    # 只保留长度为length的单词
                    for word in list(word_dict.keys()):
                        if len(word) != length:
                            del word_dict[word]

            # 随机选一个单词
            word = random.choice(list(word_dict.keys()))
            global explanation
            explanation = word_dict[word]["中释"]

            logger.info(f"选择了{word}单词，长度{length}，释义为{explanation}")

            return word.upper()
        
        except Exception as e:
            logger.error(f"加载词表失败: {e!s}")
            return None

    @command_group("wordle")  # noqa: F405
    def wordle(self):
        pass

    @wordle.command("start")  # type: ignore
    async def start_wordle(self, event: AstrMessageEvent, length: int = 5):
        """开始Wordle游戏"""
        answer = await self.get_answer(length)
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions:
            del self.game_sessions[session_id]
        if not answer:
            yield event.plain_result(f"未找到长度为{length}的单词")
        else:
            game = WordleGame(answer)
            self.game_sessions[session_id] = game
            logger.debug(f"答案是：{answer}")

    @wordle.command("stop")  # type: ignore
    async def stop_wordle(self, event: AstrMessageEvent):
        """中止Wordle游戏"""
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions:
            del self.game_sessions[session_id]
            yield event.plain_result("已结束当前游戏")
        else:
            yield event.plain_result("当前未开始游戏")

    @wordle.command("hint")  # type: ignore
    async def give_hint(self, event: AstrMessageEvent):
        """获取提示（第一个字母）"""
        session_id = event.unified_msg_origin
        if session_id not in self.game_sessions:
            yield event.plain_result("当前未开始游戏")
            return
            
        game = self.game_sessions[session_id]
        hint = f"提示: 第一个字母是 {game.answer[0]}"
        yield event.plain_result(hint)

    @event_message_type(EventMessageType.ALL)  # noqa: F405
    async def on_all_message(self, event: AstrMessageEvent):
        msg = event.get_message_str()
        session_id = event.unified_msg_origin
        if session_id in self.game_sessions and event.is_at_or_wake_command:
            game = self.game_sessions[session_id]

            if msg.startswith("wordle start"):
                yield event.plain_result("游戏已开始，请输入猜测")
                return
            
            if msg.startswith("wordle hint"):
                return

            length = game.length
            if len(msg) != length:
                yield event.plain_result(f"输入单词长度应该为{length}")
                return
            
            # 单词拼写检查
            spellcheck = SpellChecker()
            if not (
                msg in list(word_dict.keys())
                or spellcheck.known((msg,))
                ):   
                yield event.plain_result(f"请输入拼写正确的单词")
                return

            if not msg.isalpha():
                yield event.plain_result("输入应该是英文")
                return

            image_result = await game.guess(msg)

            if game.is_won:
                sender_info = event.get_sender_name() if event.get_sender_name() else event.get_sender_id()
                game_status = f"恭喜{sender_info}猜对了！正确答案是“{game.answer}”，意思是“{explanation}”"
                del self.game_sessions[session_id]
            elif game.is_game_over:
                game_status = f"游戏结束。正确答案是“{game.answer}”,意思是“{explanation}”"
                del self.game_sessions[session_id]
            else:
                game_status = f"已猜测 {len(game.guesses)}/{game.max_attempts} 次"

            chain = [
                Image.fromBytes(image_result),  # noqa: F405
                Plain(game_status),  # noqa: F405
            ]

            yield event.chain_result(chain)
