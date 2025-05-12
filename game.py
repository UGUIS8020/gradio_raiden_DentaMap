import gradio as gr
import math
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import json
import os
from datetime import datetime

# データ保存用のファイル
DATA_FILE = "dental_patterns.json"

# 初期データの読み込みまたは作成
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"patterns": {}, "total_submissions": 0, "rare_patterns": []}

# データの保存
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 歯のパターンをキーに変換
def pattern_to_key(pattern):
    return "".join([str(int(x)) for x in pattern])

# 歯の図を作成する関数
def create_dental_chart(pattern=None):
    if pattern is None:
        pattern = np.ones(28, dtype=bool)  # すべての歯がある状態
    
    # 歯の状態（1が歯あり、0が欠損）
    upper_teeth = pattern[:14]
    lower_teeth = pattern[14:]
    
    # 上下の歯の位置を定義
    positions = np.arange(1, 15)
    
    fig = Figure(figsize=(10, 6))
    ax = fig.subplots()
    
    # 上の歯を描画
    ax.scatter(positions, np.ones(14) * 1, s=300, 
               color=['white' if t else 'lightgray' for t in upper_teeth], 
               edgecolors='black', zorder=2)
    
    # 下の歯を描画
    ax.scatter(positions, np.ones(14) * -1, s=300, 
               color=['white' if t else 'lightgray' for t in lower_teeth], 
               edgecolors='black', zorder=2)
    
    # 歯茎を描画
    ax.fill_between(np.linspace(0.5, 14.5, 100), 0.7, 1.3, color='pink', alpha=0.5, zorder=1)
    ax.fill_between(np.linspace(0.5, 14.5, 100), -0.7, -1.3, color='pink', alpha=0.5, zorder=1)
    
    # 歯の番号を追加
    for i, pos in enumerate(positions):
        ax.text(pos, 1.5, str(i+1), ha='center')
        ax.text(pos, -1.5, str(i+15), ha='center')
    
    ax.set_xlim(0, 15)
    ax.set_ylim(-2, 2)
    ax.axis('off')
    ax.set_title('歯の状態（グレーは欠損）')
    
    return fig

# 組み合わせ数の計算
def calculate_combinations(n):
    return math.comb(28, n)

# 稀少度スコアの計算（0~100）
def calculate_rarity_score(pattern_key, data):
    if pattern_key in data["patterns"]:
        occurrence = data["patterns"][pattern_key]["count"]
        total = data["total_submissions"]
        if total == 0:
            return 100
        # 出現回数が少ないほどスコアが高い
        return min(100, int(100 * (1 - (occurrence / total) ** 0.5)))
    return 100  # 初めてのパターン

# パターンの提出処理
def submit_pattern(pattern, name, age, data):
    pattern_key = pattern_to_key(pattern)
    missing_count = 28 - sum(pattern)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # データの更新
    if pattern_key in data["patterns"]:
        data["patterns"][pattern_key]["count"] += 1
        data["patterns"][pattern_key]["submissions"].append({
            "name": name,
            "age": age,
            "timestamp": current_time
        })
    else:
        data["patterns"][pattern_key] = {
            "count": 1,
            "missing_count": int(missing_count),
            "pattern": [bool(p) for p in pattern],
            "submissions": [{
                "name": name,
                "age": age,
                "timestamp": current_time
            }]
        }
    
    data["total_submissions"] += 1
    
    # 稀少パターンの更新
    rarity_score = calculate_rarity_score(pattern_key, data)
    if rarity_score > 90:  # 稀少度90以上を記録
        if pattern_key not in [p["pattern_key"] for p in data["rare_patterns"]]:
            data["rare_patterns"].append({
                "pattern_key": pattern_key,
                "rarity_score": rarity_score,
                "discovered_by": name,
                "timestamp": current_time
            })
            # 稀少パターン上位10件のみ保持
            data["rare_patterns"] = sorted(data["rare_patterns"], 
                                           key=lambda x: x["rarity_score"], 
                                           reverse=True)[:10]
    
    save_data(data)
    return data, rarity_score

# 統計情報の図を作成
def create_stats_chart(data):
    if data["total_submissions"] == 0:
        fig = Figure(figsize=(10, 6))
        ax = fig.subplots()
        ax.text(0.5, 0.5, "データがありません", ha='center', va='center', fontsize=14)
        ax.axis('off')
        return fig
    
    # 欠損数ごとの分布
    missing_counts = {}
    for pattern_info in data["patterns"].values():
        count = pattern_info["missing_count"]
        if count in missing_counts:
            missing_counts[count] += pattern_info["count"]
        else:
            missing_counts[count] = pattern_info["count"]
    
    # 欠損数ごとの理論上の組み合わせ数
    theoretical_counts = {i: calculate_combinations(i) for i in range(29)}
    
    # 欠損数ごとの発見率
    discovery_rates = {}
    for i in range(29):
        if i in missing_counts:
            actual_patterns = len([p for p in data["patterns"].values() if p["missing_count"] == i])
            discovery_rates[i] = (actual_patterns / theoretical_counts[i]) * 100
        else:
            discovery_rates[i] = 0
    
    # グラフの作成
    fig = Figure(figsize=(12, 10))
    
    # 欠損数ごとの提出数
    ax1 = fig.add_subplot(2, 1, 1)
    x = list(range(29))
    heights = [missing_counts.get(i, 0) for i in x]
    ax1.bar(x, heights)
    ax1.set_title('欠損数ごとの提出数')
    ax1.set_xlabel('欠損数')
    ax1.set_ylabel('提出数')
    ax1.set_xticks(x)
    
    # 発見率のグラフ
    ax2 = fig.add_subplot(2, 1, 2)
    discovery_rates_list = [discovery_rates.get(i, 0) for i in x]
    ax2.bar(x, discovery_rates_list)
    ax2.set_title('欠損パターン発見率（理論値に対する割合）')
    ax2.set_xlabel('欠損数')
    ax2.set_ylabel('発見率 (%)')
    ax2.set_xticks(x)
    ax2.set_ylim(0, 100)
    
    fig.tight_layout()
    return fig

# ランダムなパターンを生成（テスト用）
def generate_random_pattern(missing_count):
    pattern = np.ones(28, dtype=bool)
    missing_indices = random.sample(range(28), missing_count)
    for idx in missing_indices:
        pattern[idx] = False
    return pattern

# 稀少パターンの表を作成
def create_rare_patterns_html(data):
    if not data["rare_patterns"]:
        return "<p>まだ稀少パターンは発見されていません。</p>"
    
    html = "<h3>稀少パターン発見ランキング</h3>"
    html += "<table style='width:100%; border-collapse:collapse;'>"
    html += "<tr style='background-color:#f2f2f2;'><th>順位</th><th>発見者</th><th>稀少度</th><th>欠損数</th><th>発見日時</th></tr>"
    
    for i, rare in enumerate(data["rare_patterns"]):
        pattern_key = rare["pattern_key"]
        pattern_info = data["patterns"].get(pattern_key, {})
        missing_count = pattern_info.get("missing_count", "不明")
        
        html += f"<tr style='border-bottom:1px solid #ddd;'>"
        html += f"<td style='padding:8px;text-align:center;'>{i+1}</td>"
        html += f"<td style='padding:8px;'>{rare['discovered_by']}</td>"
        html += f"<td style='padding:8px;text-align:center;'>{rare['rarity_score']}</td>"
        html += f"<td style='padding:8px;text-align:center;'>{missing_count}</td>"
        html += f"<td style='padding:8px;'>{rare['timestamp']}</td>"
        html += "</tr>"
    
    html += "</table>"
    return html

# メインアプリケーション
def create_dental_game_app():
    data = load_data()
    
    with gr.Blocks(title="歯の欠損パターン収集ゲーム") as app:
        gr.Markdown("# 🦷 歯の欠損パターン収集ゲーム 🦷")
        gr.Markdown("世界中の歯の欠損パターンを収集して、稀少なパターンを発見しよう！")
        
        with gr.Tab("パターン登録"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### あなたの歯の状態を入力")
                    gr.Markdown("各歯の状態をクリックして変更できます（グレーが欠損）")
                    
                    # 歯のパターン入力用のチェックボックス
                    teeth_checkboxes = []
                    with gr.Row():
                        gr.Markdown("### 上顎")
                    with gr.Row():
                        for i in range(14):
                            cb = gr.Checkbox(label=str(i+1), value=True)
                            teeth_checkboxes.append(cb)
                    
                    with gr.Row():
                        gr.Markdown("### 下顎")
                    with gr.Row():
                        for i in range(14, 28):
                            cb = gr.Checkbox(label=str(i+1), value=True)
                            teeth_checkboxes.append(cb)
                    
                    name_input = gr.Textbox(label="ニックネーム（発見者として記録されます）")
                    age_input = gr.Number(label="年齢（任意・統計用）", minimum=0, maximum=120)
                    
                    with gr.Row():
                        random_btn = gr.Button("ランダムパターン生成（テスト用）")
                        clear_btn = gr.Button("リセット")
                        submit_btn = gr.Button("パターン登録", variant="primary")
                
                with gr.Column():
                    chart_output = gr.Plot(label="歯の状態プレビュー")
                    missing_output = gr.Textbox(label="欠損数", interactive=False)
                    combinations_output = gr.Textbox(label="同じ欠損数の組み合わせ数", interactive=False)
                    
                    with gr.Group():
                        result_markdown = gr.Markdown("登録結果がここに表示されます")
            
            # パターン更新時の処理
            def update_chart(*checkbox_values):
                pattern = np.array(checkbox_values, dtype=bool)
                fig = create_dental_chart(pattern)
                missing_count = 28 - sum(pattern)
                combinations = calculate_combinations(missing_count)
                return fig, f"{missing_count} 本", f"{combinations:,} 通り"
            
            # すべてのチェックボックスの変更をプレビューに反映
            for cb in teeth_checkboxes:
                cb.change(
                    fn=update_chart,
                    inputs=teeth_checkboxes,
                    outputs=[chart_output, missing_output, combinations_output]
                )
            
            # ランダムパターン生成
            def generate_random_ui():
                missing_count = random.randint(0, 10)  # 0〜10本の欠損をランダムに
                pattern = generate_random_pattern(missing_count)
                return list(pattern)
            
            random_btn.click(
                fn=generate_random_ui,
                inputs=[],
                outputs=teeth_checkboxes
            )
            
            # リセット
            def reset_pattern():
                return [True] * 28
            
            clear_btn.click(
                fn=reset_pattern,
                inputs=[],
                outputs=teeth_checkboxes
            )
            
            # パターン登録処理
            def submit_pattern_ui(*checkbox_values, name, age):
                pattern = np.array(checkbox_values, dtype=bool)
                if not name:
                    return "ニックネームを入力してください。"
                
                nonlocal data
                data, rarity_score = submit_pattern(pattern, name, age, data)
                
                missing_count = 28 - sum(pattern)
                pattern_key = pattern_to_key(pattern)
                count = data["patterns"][pattern_key]["count"]
                
                if count > 1:
                    message = f"このパターンは{count}回目の登録です。"
                else:
                    message = "新しいパターンを発見しました！"
                
                if rarity_score > 90:
                    message += f"\n\n🏆 おめでとう！稀少度 {rarity_score} の珍しいパターンを発見しました！"
                elif rarity_score > 70:
                    message += f"\n\nすごい！稀少度 {rarity_score} のやや珍しいパターンです。"
                else:
                    message += f"\n\n稀少度: {rarity_score}"
                
                message += f"\n\n現在の総登録数: {data['total_submissions']}"
                message += f"\n発見された一意なパターン数: {len(data['patterns'])}"
                message += f"\n理論上可能なパターン数: {2**28:,}"
                
                return message
            
            submit_btn.click(
                fn=submit_pattern_ui,
                inputs=teeth_checkboxes + [name_input, age_input],
                outputs=result_markdown
            )
        
        with gr.Tab("統計情報"):
            gr.Markdown("### 収集されたデータの統計")
            
            refresh_stats_btn = gr.Button("統計を更新")
            stats_chart = gr.Plot(label="統計グラフ")
            submissions_info = gr.Markdown()
            
            def update_stats():
                nonlocal data
                data = load_data()  # 最新データを読み込み
                fig = create_stats_chart(data)
                
                unique_patterns = len(data["patterns"])
                total_submissions = data["total_submissions"]
                theoretical_total = 2**28
                
                info = f"### 現在の進捗\n"
                info += f"総登録数: {total_submissions}\n\n"
                info += f"一意なパターン数: {unique_patterns:,}\n\n"
                info += f"発見率: {(unique_patterns / theoretical_total) * 100:.10f}%\n\n"
                info += f"理論上可能なパターン数: {theoretical_total:,}"
                
                return fig, info
            
            refresh_stats_btn.click(
                fn=update_stats,
                inputs=[],
                outputs=[stats_chart, submissions_info]
            )
            
            rare_patterns_html = gr.HTML()
            
            def update_rare_patterns():
                nonlocal data
                data = load_data()
                return create_rare_patterns_html(data)
            
            refresh_stats_btn.click(
                fn=update_rare_patterns,
                inputs=[],
                outputs=rare_patterns_html
            )
        
        with gr.Tab("ゲーム説明"):
            gr.Markdown("""
            # 歯の欠損パターン収集ゲームのルール
            
            ## 目的
            人間の永久歯（親知らずを除く）は上下合わせて28本あります。その歯の有無のパターンは2^28 = 268,435,456通り存在します。
            このゲームでは、実際に存在する歯の欠損パターンを世界中から収集し、どのようなパターンがあるのかを調査します。
            
            ## 参加方法
            1. 「パターン登録」タブで、あなたや知人の歯の欠損状態を入力します
            2. ニックネームを入力して登録すると、そのパターンの稀少度がわかります
            3. とても珍しいパターンを発見すると、ランキングに載ることができます
            
            ## 稀少度スコア
            稀少度は0〜100のスコアで表され、そのパターンの登録回数と総登録数から計算されます。
            初めて登録されたパターンは稀少度100となります。
            
            ## 注意事項
            - このデータは研究・教育目的で収集されています
            - 個人を特定できる情報は入力しないでください
            - テスト目的で「ランダムパターン生成」機能がありますが、実際の歯の状態を登録することをお勧めします
            
            一人でも多くの方の参加をお待ちしています！
            """)
    
    # 初期表示用のセットアップ
    app.load(
        fn=update_chart,
        inputs=teeth_checkboxes,
        outputs=[chart_output, missing_output, combinations_output]
    )
    
    app.load(
        fn=update_stats,
        inputs=[],
        outputs=[stats_chart, submissions_info]
    )
    
    app.load(
        fn=update_rare_patterns,
        inputs=[],
        outputs=rare_patterns_html
    )
    
    return app

# アプリの起動
if __name__ == "__main__":
    dental_app = create_dental_game_app()
    dental_app.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        show_error=True
    )