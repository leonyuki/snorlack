import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge

# 1. データの読み込み
df = pd.read_csv("snorlax_data.csv")

# 2. テキストを数値ベクトル（TF-IDF）に変換するモデル
vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 3))
X = vectorizer.fit_transform(df['text'])

# 3. 目的変数（予測したい3つの数値）
y = df[['dS', 'dH', 'dI']].values

# 4. 機械学習モデル（Ridge回帰）の学習
model = Ridge(alpha=1.0)
model.fit(X, y)

# 5. 学習済みモデルとベクタライザをファイルに保存（これがカビゴンの脳になります）
with open('snorlax_brain.pkl', 'wb') as f:
    pickle.dump({'vectorizer': vectorizer, 'model': model}, f)

print("✅ 学習が完了し、パラメータを snorlax_brain.pkl に保存しました！")