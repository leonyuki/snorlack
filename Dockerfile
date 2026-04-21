# 軽量なPython 3.11イメージを使用
FROM python:3.11-slim

# 作業ディレクトリを /code に設定
WORKDIR /code

# ライブラリの設計図をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# プログラム本体（main.py）と学習済みデータ（snorlax_brain.pkl）をコピー
COPY . .

# Hugging Face Spacesの規定ポート 7860 でサーバーを起動
# $PORT という変数を使わず、直接 7860 を指定するのがHFのコツです
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
