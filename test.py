import gradio as gr
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import io
import base64

# 歯の配列定義（歯科番号）
UPPER_TEETH = list(range(11, 19)) + list(range(21, 29))  # 上顎
LOWER_TEETH = list(range(31, 39)) + list(range(41, 49))  # 下顎

def calculate_combinations(upper_missing, lower_missing):
    """欠損パターンの組み合わせ数を計算"""
    upper_comb = math.comb(14, upper_missing) if 0 <= upper_missing <= 14 else 0
    lower_comb = math.comb(14, lower_missing) if 0 <= lower_missing <= 14 else 0
    total_combinations = upper_comb * lower_comb
    
    return (
        f"上顎：{upper_missing}本欠損時の組み合わせ = {upper_comb:,}通り\n"
        f"下顎：{lower_missing}本欠損時の組み合わせ = {lower_comb:,}通り\n"
        f"合計組み合わせ数 = {total_combinations:,}通り"
    )

def create_dental_chart(missing_pattern):
    """欠損パターンを可視化"""
    fig = Figure(figsize=(12, 8))
    ax = fig.add_subplot(111)
    
    # 歯の描画関数
    def draw_tooth(ax, position, tooth_number, is_missing):
        if position < 8:  # 上顎
            x, y = position * 1.5, 3
        else:  # 下顎
            x, y = (position - 8) * 1.5, 1
            
        # 歯の形を描画
        color = 'lightgray' if is_missing else 'white'
        tooth = patches.Rectangle((x-0.6, y-0.4), 1.2, 0.8, 
                                 linewidth=1, edgecolor='black', 
                                 facecolor=color)
        ax.add_patch(tooth)
        
        # 歯番を表示
        text_color = 'red' if is_missing else 'black'
        ax.text(x, y, str(tooth_number), ha='center', va='center',
               fontsize=10, color=text_color, weight='bold')
    
    # 上顎右側（11-18）
    for i, tooth_num in enumerate(range(18, 10, -1)):
        draw_tooth(ax, i, tooth_num, tooth_num in missing_pattern)
    
    # 上顎左側（21-28）  
    for i, tooth_num in enumerate(range(21, 29)):
        draw_tooth(ax, i, tooth_num, tooth_num in missing_pattern)
    
    # 下顎右側（41-48）
    for i, tooth_num in enumerate(range(48, 40, -1)):
        draw_tooth(ax, i+8, tooth_num, tooth_num in missing_pattern)
    
    # 下顎左側（31-38）
    for i, tooth_num in enumerate(range(31, 39)):
        draw_tooth(ax, i+8, tooth_num, tooth_num in missing_pattern)
    
    # グラフのスタイル設定
    ax.set_xlim(-1, 12)
    ax.set_ylim(0, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('歯列図（欠損歯は灰色で表示）', fontsize=16, fontweight='bold')
    
    # 凡例
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='white', edgecolor='black', label='健在歯'),
                      Patch(facecolor='lightgray', edgecolor='black', label='欠損歯')]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # PNGに変換
    canvas = FigureCanvasAgg(fig)
    png_image = io.BytesIO()
    canvas.print_png(png_image)
    png_image.seek(0)
    return base64.b64encode(png_image.getvalue()).decode('utf-8')

def parse_missing_teeth(missing_input):
    """入力された欠損歯番号をパース"""
    try:
        if not missing_input:
            return []
        # カンマ区切りで歯番を受け取り、整数リストに変換
        return [int(x.strip()) for x in missing_input.split(',')]
    except:
        return []

def update_chart(missing_teeth_str):
    """欠損パターンの可視化を更新"""
    missing_pattern = parse_missing_teeth(missing_teeth_str)
    
    # 上下顎の欠損数カウント
    upper_missing = len([t for t in missing_pattern if 11 <= t <= 28])
    lower_missing = len([t for t in missing_pattern if 31 <= t <= 48])
    
    # 組み合わせ数計算
    combinations_text = calculate_combinations(upper_missing, lower_missing)
    
    # 歯列図生成
    chart_base64 = create_dental_chart(missing_pattern)
    chart_html = f'<img src="data:image/png;base64,{chart_base64}" alt="歯列図">'
    
    # 欠損状態サマリー
    summary = f"""
    【欠損状態サマリー】
    合計欠損歯数：{len(missing_pattern)}本
    上顎欠損：{upper_missing}本
    下顎欠損：{lower_missing}本
    
    欠損歯番号：{', '.join(map(str, sorted(missing_pattern)))}
    """
    
    return chart_html, combinations_text, summary

# UIの構築
with gr.Blocks(title="歯列欠損パターン可視化システム") as demo:
    gr.Markdown("# 歯列欠損パターン可視化システム")
    gr.Markdown("""
    このシステムは歯科番号を使用して欠損パターンを可視化し、
    可能な組み合わせ数を計算します。
    
    **使用方法：**
    - 欠損している歯番号をカンマ区切りで入力してください
    - 例：11,12,26,31 (上顎：11番、12番、26番、下顎：31番が欠損)
    """)
    
    with gr.Row():
        with gr.Column():
            missing_input = gr.Textbox(
                label="欠損歯番号（カンマ区切り）",
                placeholder="例：11,12,26,31",
                value="11,12,26,31"
            )
            
            # クイック入力ボタン
            gr.Markdown("**クイック入力：**")
            example_btn = gr.Button("全歯欠損（総義歯）")
            partial_btn = gr.Button("部分義歯（上顎右側）")
            
            def set_total_missing():
                all_teeth = list(range(11, 19)) + list(range(21, 29)) + \
                           list(range(31, 39)) + list(range(41, 49))
                return ",".join(map(str, all_teeth))
            
            def set_partial_missing():
                return "14,15,16,17,18"
            
            example_btn.click(fn=set_total_missing, outputs=missing_input)
            partial_btn.click(fn=set_partial_missing, outputs=missing_input)
        
        with gr.Column():
            chart_output = gr.HTML(label="歯列図")
            combinations_output = gr.Textbox(label="組み合わせ数", lines=3)
            summary_output = gr.Textbox(label="欠損状態サマリー", lines=5)
    
    # 自動更新
    missing_input.change(
        fn=update_chart, 
        inputs=missing_input, 
        outputs=[chart_output, combinations_output, summary_output]
    )
    
    # 初期表示
    demo.load(
        fn=update_chart,
        inputs=missing_input,
        outputs=[chart_output, combinations_output, summary_output]
    )

# アプリケーションの起動
if __name__ == "__main__":
    demo.launch(
        
        server_name="127.0.0.1",  # 全てのネットワークインターフェースからアクセス可能
        server_port=7860,       # デフォルトポート
        share=False             # 公開リンクを使用しない
    )