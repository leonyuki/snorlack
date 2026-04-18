import pickle
import random
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from janome.tokenizer import Tokenizer  # 👈 新しく追加！

# ==========================================
# 1. 各種設定
# ==========================================
line_bot_api = LineBotApi("HMk1z+vPBkrkIIzpebxux9Zhgu3ZL4sKx7dWhBAzdCv7Aha8X72VnCA2BpEDzVWxszS0O6+NfloUyErNQlsfVwEryx8cYn4Fd8mXZoU5GzmzdY0Rd9Fa0hj9Qyxgtj0cBmaLJRCtMaM3j0BENUnw/QdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("207e322f2f2be98cc2af53182cc581b7")

app = FastAPI()

# ==========================================
# 2. カビゴンの頭脳（形態素解析搭載モデル）
# ==========================================
class SnorlaxModel:
    def __init__(self):
        self.S = 90
        self.H = 50
        self.I = 0
        
        # 学習済みのモデルを読み込む
        with open('snorlax_brain.pkl', 'rb') as f:
            brain = pickle.load(f)
            self.vectorizer = brain['vectorizer']
            self.model = brain['model']

        # 👈 Janomeのトークナイザー（文章を単語に分解するハサミ）を準備
        self.tokenizer = Tokenizer()
        
        # 状態別のテンプレート
        self.templates = {
            "sleeping": [
                "「グー…ズー…」（深い寝息を立てている）",
                "「スピー…」（幸せそうに眠っている）",
                "「ムニャ…{word}…」（寝言で呟いている）"
            ],
            "hungry": [
                "「カビカビ！」（{word}の匂いを嗅ぎつけて、盛大にお腹を鳴らした）",
                "「カビッ！」（{word}をよだれを垂らして見つめている）",
                "「カビ〜…」（{word}を食べたそうに口を開けている）"
            ],
            "angry": [
                "「ゴンッ！」（{word}に苛立って、ドスンドスンと地響きを立てた）",
                "「カビ…！！」（不機嫌そうにそっぽを向いた）"
            ],
            "normal_awake": [
                "「カビ？」（{word}と聞いて、不思議そうに首をかしげた）",
                "「カビカビ」（のんびりとあくびをした）",
                "「カビッ」（{word}に少し興味を示して、座り直した）"
            ]
        }

    def extract_keyword(self, text):
        """文章からカビゴンが反応すべき「名詞」を抽出する"""
        # 文章を単語に分解して、一つずつチェック
        for token in self.tokenizer.tokenize(text):
            # 品詞情報をカンマで分割（例: "名詞,一般,*,*,*,*,りんご,リンゴ,リンゴ"）
            pos = token.part_of_speech.split(',')
            
            # 品詞が「名詞」であり、かつ「代名詞(私,これ等)」「数(100等)」「非自立(こと,もの等)」でないものを採用
            if pos[0] == '名詞' and pos[1] not in ['代名詞', '数', '非自立', '接尾']:
                return token.surface # 見つけた名詞の文字列を返す
        
        return "それ" # 良い名詞が見つからなかった場合のデフォルト

    def generate_response(self, user_text):
        # 👈 辞書ではなく、形態素解析で動的に単語を抽出！
        extracted_word = self.extract_keyword(user_text)

        # 現在のパラメータから「今の状態（機嫌）」を判定
        if self.S > 50:
            state_category = "sleeping"
        elif self.H > 70:
            state_category = "hungry"
        elif self.I > 60:
            state_category = "angry"
        else:
            state_category = "normal_awake"

        # 該当する状態の回答集からランダムに1つ選び、単語を埋め込む
        chosen_template = random.choice(self.templates[state_category])
        final_text = chosen_template.format(word=extracted_word)
        
        return final_text

    def calculate_state(self, user_text):
        """状態推移を計算し、テキストを生成する"""
        X_input = self.vectorizer.transform([user_text])
        predictions = self.model.predict(X_input)[0]
        
        dS, dH, dI = predictions
        
        self.S = max(0, min(100, self.S + dS))
        self.H = max(0, min(100, self.H + dH + 5))
        self.I = max(0, min(100, self.I + dI))
        
        print(f"📊 現在のステータス -> S:{self.S:.1f}, H:{self.H:.1f}, I:{self.I:.1f}")
        
        return self.generate_response(user_text)

snorlax = SnorlaxModel()

# ==========================================
# 3. LINE通信部分
# ==========================================
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    try:
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    print(f"\n💬 ユーザー: {user_text}")
    
    response_text = snorlax.calculate_state(user_text)
    print(f"💤 カビゴン: {response_text}")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_text)
    )