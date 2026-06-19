"""
J-Genom DIアルゴリズム テストスイート
"""
import pytest
from di.di import count_morae, count_kanji, levenshtein, avg_stroke_count, get_rarity_score, calculate_di


# ── ① count_morae ──────────────────────────────────────────────

class TestCountMorae:
    def test_basic_hiragana(self):
        assert count_morae('ばら') == 2

    def test_digraph_counts_as_one(self):
        # きゃ = 1モーラ
        assert count_morae('きゃく') == 2  # きゃ + く

    def test_long_reading(self):
        assert count_morae('さみだれ') == 4

    def test_katakana_converted(self):
        assert count_morae('トウキョウ') == count_morae('とうきょう')

    def test_minimum_one(self):
        # 空文字でも最低1を返す
        assert count_morae('') == 1

    def test_multiple_digraphs(self):
        assert count_morae('しののめ') == 4  # し・の・の・め


# ── ② count_kanji ──────────────────────────────────────────────

class TestCountKanji:
    def test_pure_kanji(self):
        assert count_kanji('薔薇') == 2

    def test_mixed_string(self):
        assert count_kanji('小鳥遊') == 3

    def test_no_kanji(self):
        assert count_kanji('ばら') == 0

    def test_single_kanji(self):
        assert count_kanji('一') == 1

    def test_kanji_with_hiragana(self):
        assert count_kanji('五月雨') == 3


# ── levenshtein ────────────────────────────────────────────────

class TestLevenshtein:
    def test_identical_strings(self):
        assert levenshtein('ばら', 'ばら') == 0

    def test_empty_strings(self):
        assert levenshtein('', '') == 0

    def test_one_empty(self):
        assert levenshtein('ばら', '') == 2

    def test_single_substitution(self):
        assert levenshtein('ばら', 'はら') == 1

    def test_insertion(self):
        assert levenshtein('ばら', 'ばらら') == 1

    def test_completely_different(self):
        # もぐら vs むぐらもち
        assert levenshtein('もぐら', 'むぐらもち') > 0


# ── ③ avg_stroke_count ─────────────────────────────────────────

class TestAvgStrokeCount:
    def test_complex_kanji(self):
        # 薔(16画)薇(16画) → 平均16
        assert avg_stroke_count('薔薇') == 16.0

    def test_simple_kanji(self):
        # 一 = 1画
        assert avg_stroke_count('一') == 1.0

    def test_no_kanji(self):
        assert avg_stroke_count('ばら') == 0.0

    def test_average_of_multiple(self):
        # 土(3画) + 竜(10画) → 平均6.5
        assert avg_stroke_count('土竜') == 6.5


# ── ④ get_rarity_score ─────────────────────────────────────────

class TestGetRarityScore:
    def test_common_word_is_low(self):
        # 電話(でんわ) は nf01 = 非常に一般的
        score = get_rarity_score('電話', 'でんわ')
        assert score < 0.1

    def test_not_in_dict_is_max(self):
        # 辞書にない文字列 → 1.0
        assert get_rarity_score('小鳥遊', 'たかなし') == 1.0

    def test_reading_mismatch_is_high(self):
        # 辞書にあるが読みが異なる → 0.9
        score = get_rarity_score('一', 'にのまえ')
        assert score == 0.9

    def test_rare_word_is_high(self):
        # 東雲(しののめ) は頻度マーカーなし → 高スコア
        score = get_rarity_score('東雲', 'しののめ')
        assert score >= 0.8


# ── calculate_di 統合テスト ────────────────────────────────────

class TestCalculateDI:
    def test_returns_required_keys(self):
        result = calculate_di('薔薇', 'ばら')
        expected_keys = {
            'text', 'reading', 'machine_reading',
            'kanji_count', 'mora_count', 'avg_strokes',
            'mora_kanji_ratio', 'penalty_factor',
            'score_ratio', 'score_prediction', 'score_strokes', 'score_rarity',
            'di_score'
        }
        assert expected_keys == set(result.keys())

    def test_score_in_range(self):
        for text, reading in [('東京', 'とうきょう'), ('薔薇', 'ばら'), ('一', 'にのまえ')]:
            result = calculate_di(text, reading)
            assert 0.0 <= result['di_score'] <= 100.0

    def test_ordering_low_to_high(self):
        # 直感的な乖離の順序が保たれているか
        tokio   = calculate_di('東京',   'とうきょう')
        bara    = calculate_di('薔薇',   'ばら')
        mogura  = calculate_di('土竜',   'もぐら')
        ninomae = calculate_di('一',     'にのまえ')

        assert tokio['di_score'] < bara['di_score']
        assert bara['di_score']  < mogura['di_score']
        assert mogura['di_score'] < ninomae['di_score']

    def test_complete_divergence_is_high(self):
        # 完全乖離（一→にのまえ）は高スコア
        result = calculate_di('一', 'にのまえ')
        assert result['di_score'] >= 80.0

    def test_common_word_is_low(self):
        # 一般的な単語（東京）は低スコア
        result = calculate_di('東京', 'とうきょう')
        assert result['di_score'] < 10.0


# ── 長すぎる読みへのペナルティ ────────────────────────────────

class TestLongReadingPenalty:
    def test_no_penalty_within_threshold(self):
        # 一→にのまえ: 比率4.0 < 閾値5.0 → ペナルティなし
        result = calculate_di('一', 'にのまえ')
        assert result['penalty_factor'] == 1.0

    def test_penalty_applied_above_threshold(self):
        # 比率が5.0を超えるとペナルティが発動
        result = calculate_di('一', 'あいうえおかきくけこ')  # 10モーラ / 1漢字 = 10.0
        assert result['penalty_factor'] < 1.0

    def test_penalty_reduces_score(self):
        # ペナルティありの方がスコアが低くなる
        legit   = calculate_di('一', 'にのまえ')        # ratio 4.0
        abusive = calculate_di('一', 'あいうえおかきくけこ')  # ratio 10.0
        assert abusive['di_score'] < legit['di_score']

    def test_penalty_factor_formula(self):
        # ratio=10.0 → penalty_factor = 5.0/10.0 = 0.5
        result = calculate_di('一', 'あいうえおかきくけこ')
        assert result['mora_kanji_ratio'] == 10.0
        assert abs(result['penalty_factor'] - 0.5) < 0.01
