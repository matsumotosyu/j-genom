#!/usr/bin/env python3
"""
Divergence Index (DI) — J-Genom プロジェクト
文字と読みの乖離度を定量化する。

計算要素:
  ① 文字数とモーラ数の比率ズレ
  ② 機械推定読みとユーザー登録読みの乖離（編集距離）
  ③ 平均画数スコア（非ネイティブ視点の視覚的複雑さ）
  ④ 一般認知度の逆数（語彙頻度ランキングから算出）
"""

import pykakasi
import jaconv
from jamdict import Jamdict

_kks = pykakasi.kakasi()
_jmd = Jamdict()


def count_morae(reading: str) -> int:
    """ひらがな/カタカナ文字列のモーラ数を数える。"""
    reading = jaconv.kata2hira(reading)
    small_vowels = set('ぁぃぅぇぉゃゅょゎ')
    count = 0
    i = 0
    while i < len(reading):
        if i + 1 < len(reading) and reading[i + 1] in small_vowels:
            count += 1
            i += 2
        else:
            count += 1
            i += 1
    return max(count, 1)


def count_kanji(text: str) -> int:
    """CJK統合漢字の文字数を数える。"""
    return sum(
        1 for c in text
        if '一' <= c <= '鿿' or '㐀' <= c <= '䶿'
    )


def avg_stroke_count(text: str) -> float:
    """漢字の平均画数を返す。辞書にない文字は除外する。"""
    strokes = []
    for char in text:
        if not ('一' <= char <= '鿿' or '㐀' <= char <= '䶿'):
            continue
        info = _jmd.lookup(char)
        if info.chars and info.chars[0].stroke_count:
            strokes.append(info.chars[0].stroke_count)
    return sum(strokes) / len(strokes) if strokes else 0.0


def get_rarity_score(text: str, reading: str) -> float:
    """
    一般認知度の逆数スコアを返す（0=よく知られている, 1=非常に希少）。

    JMdict の nf01-nf48 頻度マーカーを使用。
    読みがエントリの読み形式にマッチしない場合は希少とみなす。
    """
    result = _jmd.lookup(text)

    if not result.entries:
        return 1.0  # 辞書に存在しない

    # 指定された読みにマッチするエントリを探す
    matched_entry = None
    for entry in result.entries:
        for r in entry.kana_forms:
            if r.text == reading:
                matched_entry = entry
                break
        if matched_entry:
            break

    if matched_entry is None:
        # 辞書にあるが指定の読みがない = 異読（かなり希少）
        return 0.9

    # マッチしたエントリの kanji_form から nf スコアを取得
    pri = []
    for k in matched_entry.kanji_forms:
        if k.text == text:
            pri = list(k.pri)
            break

    for marker in pri:
        if marker.startswith('nf'):
            nf = int(marker[2:])
            return nf / 48.0  # nf01→0.02, nf48→1.0

    # nf マーカーなしだが辞書には存在
    if 'ichi1' in pri or 'news1' in pri:
        return 0.2
    if 'ichi2' in pri or 'news2' in pri:
        return 0.5
    return 0.85  # 辞書にあるが頻度データなし


def get_machine_reading(text: str) -> str:
    """pykakasi による推定ひらがな読みを返す。"""
    return ''.join(item['hira'] for item in _kks.convert(text))


def levenshtein(s1: str, s2: str) -> int:
    """レーベンシュタイン距離（編集距離）を計算する。"""
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n + 1):
            dp[j] = prev[j - 1] if s1[i - 1] == s2[j - 1] else 1 + min(prev[j], dp[j - 1], prev[j - 1])
    return dp[n]


def calculate_di(text: str, reading: str) -> dict:
    """
    Divergence Index を計算する。

    Args:
        text:    漢字文字列（例: "薔薇"）
        reading: 正しいひらがな読み（例: "ばら"）

    Returns:
        di_score (0〜100) と内訳を含む dict
    """
    kanji_count = count_kanji(text)
    mora_count = count_morae(reading)
    machine_reading = get_machine_reading(text)

    # スコア①: 漢字数あたりモーラ数の標準からのズレ
    # 標準的な日本語: 漢字1字 ≈ 2モーラ
    BASELINE_MORAE_PER_KANJI = 2.0
    expected_morae = kanji_count * BASELINE_MORAE_PER_KANJI
    if expected_morae > 0:
        score_ratio = min(1.0, abs(mora_count - expected_morae) / expected_morae)
    else:
        score_ratio = 0.0

    # スコア②: 機械読みとユーザー読みの編集距離
    max_len = max(len(machine_reading), len(reading), 1)
    score_prediction = min(1.0, levenshtein(machine_reading, reading) / max_len)

    # スコア③: 画数の「期待値からの乖離」（双方向）
    # 常用漢字の平均画数 ≈ 10画を基準とし、多くても少なくても乖離とみなす
    STROKE_BASELINE = 10.0
    avg_strokes = avg_stroke_count(text)
    score_strokes = min(1.0, abs(avg_strokes - STROKE_BASELINE) / STROKE_BASELINE)

    # スコア④: 一般認知度の逆数（JMdict 頻度マーカー）
    score_rarity = get_rarity_score(text, reading)

    # 加重合成（重みは今後チューニング予定）
    W1, W2, W3, W4 = 0.2, 0.4, 0.15, 0.25
    di_score = (W1 * score_ratio + W2 * score_prediction + W3 * score_strokes + W4 * score_rarity) * 100

    # 長すぎる読みへのペナルティ（閾値: 5.0モーラ/漢字）
    # 閾値を超えた分に比例して DI を減衰: penalty_factor = 5.0 / ratio
    RATIO_THRESHOLD = 5.0
    mora_kanji_ratio = mora_count / kanji_count if kanji_count > 0 else 0.0
    if mora_kanji_ratio > RATIO_THRESHOLD:
        penalty_factor = RATIO_THRESHOLD / mora_kanji_ratio
    else:
        penalty_factor = 1.0
    di_score *= penalty_factor

    return {
        'text': text,
        'reading': reading,
        'machine_reading': machine_reading,
        'kanji_count': kanji_count,
        'mora_count': mora_count,
        'avg_strokes': round(avg_strokes, 1),
        'mora_kanji_ratio': round(mora_kanji_ratio, 2),
        'penalty_factor': round(penalty_factor, 3),
        'score_ratio': round(score_ratio, 3),
        'score_prediction': round(score_prediction, 3),
        'score_strokes': round(score_strokes, 3),
        'score_rarity': round(score_rarity, 3),
        'di_score': round(di_score, 1),
    }


if __name__ == '__main__':
    test_cases = [
        # 一般的な単語（ベースライン）
        ('電話',   'でんわ'),
        ('東京',   'とうきょう'),
        # 難読漢字
        ('薔薇',   'ばら'),
        ('土竜',   'もぐら'),
        ('東雲',   'しののめ'),
        ('五月雨', 'さみだれ'),
        # 意味的当て字
        ('小鳥遊', 'たかなし'),
        # 完全乖離
        ('一',     'にのまえ'),
    ]

    print(f"{'文字列':<6} {'読み':<8} {'機械読み':<10} {'画数':>4} {'①比率':>6} {'②予測':>6} {'③画数':>6} {'④希少':>6} {'DI':>6}")
    print('─' * 72)
    for text, reading in test_cases:
        r = calculate_di(text, reading)
        print(
            f"{r['text']:<6} {r['reading']:<8} {r['machine_reading']:<10}"
            f" {r['avg_strokes']:>4.1f}"
            f" {r['score_ratio']:>6.3f} {r['score_prediction']:>6.3f}"
            f" {r['score_strokes']:>6.3f} {r['score_rarity']:>6.3f} {r['di_score']:>6.1f}"
        )
