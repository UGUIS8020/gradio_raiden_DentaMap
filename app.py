import gradio as gr
import math
import threading
from raiden.chatbot_engine import chat, get_index
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from raiden.chatbot_utils import store_response_in_pinecone, search_cached_answer
import time

# 環境変数のロード
load_dotenv()

# indexをグローバルに初期化
index = None

# チャットボットの応答関数
def respond(message, chat_history):
    global index
    start_time = time.time()    

    # ChatMessageHistory オブジェクトに現在の履歴を追加
    history = ChatMessageHistory()
    for [user_message, ai_message] in chat_history:
        history.add_user_message(user_message)
        history.add_ai_message(ai_message)

    # 1. キャッシュ検索（過去回答の検索）
    cached_result = search_cached_answer(message)
    # cached_result = {"found": False}

    if cached_result.get("found"):        
        bot_message = cached_result["answer"]
         # 応答時間を計測して表示
        elapsed_time = time.time() - start_time
        print(f"キャッシュヒット！保存済み回答を返します (応答時間: {elapsed_time:.3f}秒)")

    else:
        # 3. キャッシュヒットしなかった場合 → 新規回答を生成
        print("キャッシュヒットなし。LLMで新規回答を生成します")

        prompt = f"""
        1. 専門知識に基づき、質問に関連する情報を要約して回答してください。        
        2. 回答は日本語で作成し、結論と臨床的な参考事例を含めてください。
        3. 直接関連する情報がない場合は、最も近い情報を提供し、その旨を明示してください。
        4. 歯科医療に関する質問（歯牙移植、歯科治療、歯科技工所など）は非常に専門的であるため、必ずベクトル検索ツールを使用してください。自身の知識だけで回答せず、必ずツールを使用してください。

        質問: {message}
        """

        # indexがNoneの場合は初期化
        if index is None:
            index = get_index()

        # LLMから回答を取得
        bot_message = chat(prompt, history, index)

        # 4. 回答をPineconeに保存
        store_result = store_response_in_pinecone(message, bot_message)
        if store_result:
            print("新規回答を正常にPineconeに保存しました")

    # 5. チャット履歴を更新
    chat_history.append((message, bot_message))

    # 6. チャット履歴の最大保持数を制限
    MAX_HISTORY_LENGTH = 3
    if len(chat_history) > MAX_HISTORY_LENGTH:
        while len(chat_history) > MAX_HISTORY_LENGTH:
            chat_history.pop(0)

        # history.messagesも同様に制限
        while len(history.messages) > MAX_HISTORY_LENGTH * 2:
            history.messages.pop(0)

    return "", chat_history



# 欠損数チェッカーの関数
def calculate_combinations_28(n):
    if not (0 <= n <= 28):
        return "0〜28本の間で入力してください。"
    combinations = math.comb(28, n)
    return f"上下顎あわせて {n} 本が欠損している場合、\n組み合わせ数は {combinations:,} 通りです。"

# 欠損数チェッカーのインターフェース
with gr.Blocks(title="欠損数チェッカー") as dental_app:
    gr.Markdown("## 欠損数チェッカー（上下顎）")
    gr.Markdown("上下顎あわせて28本のうち、何本欠損したかに応じた組み合わせ数を表示します。")
    slider = gr.Slider(0, 28, step=1, value=10, label="欠損歯の本数（上下顎 合計）")
    output = gr.Textbox(label="結果", lines=2)
    slider.change(fn=calculate_combinations_28, inputs=slider, outputs=output)



# 欠損数チェッカーを起動する関数
def run_dental_app():
    print("欠損数チェッカーを起動中... (http://0.0.0.0:7861)")
    dental_app.launch(
        server_name="127.0.0.1",  # EC2では外部からのアクセスを許可するため0.0.0.0を使用
        server_port=7861,  # チャットボットをメインにするためポートを7861に変更
        share=False,
        show_error=True
    )

# メインのチャットボットアプリ
if __name__ == "__main__":
    # インデックスの初期化
    print("チャットボット用インデックスを初期化中...")
    try:
        index = get_index()
        print("インデックスの初期化が完了しました")
    except Exception as e:
        print(f"インデックス初期化エラー: {e}")
        print("警告: インデックスなしで起動します。必要時に再初期化を試みます。")
    
    # 欠損数チェッカーを別スレッドで起動
    thread = threading.Thread(target=run_dental_app)
    thread.daemon = True  # メインプログラム終了時にスレッドも終了させる
    thread.start()
    

with gr.Blocks(css=".gradio-container {background-color:rgb(248, 230, 199)}") as demo:    
    gr.Markdown("## 自家歯牙移植、歯牙再植、歯科全般について応答します")    
    gr.Markdown("""
    ### Chatbotに関するご意見,ご要望は:070-6633-0363  **email**:shibuya8020@gmail.com    
    """)    

    chatbot = gr.Chatbot(autoscroll=True)
    msg = gr.Textbox(placeholder="メッセージを入力してください", label="conversation")
    clear = gr.ClearButton([msg, chatbot])
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    
    # チャットボットを起動 (メインアプリ)
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,  # メインアプリをポート7860で起動
        share=False,
        show_error=True
    )