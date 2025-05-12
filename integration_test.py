import gradio as gr
import math
import threading
from raiden.chatbot_engine import chat, get_index
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from raiden.chatbot_utils import store_response_in_pinecone, search_cached_answer
import time
# グローバル初期化
load_dotenv()
index = None

# 欠損数チェッカー関数
def calculate_combinations_28(n):
    if not (0 <= n <= 28):
        return "0〜28本の間で入力してください。"
    combinations = math.comb(28, n)
    return f"上下顎あわせて {n} 本が欠損している場合、\n組み合わせ数は {combinations:,} 通りです。"

# チャット応答関数
def respond(message, chat_history):
    global index
    start_time = time.time()
    history = ChatMessageHistory()
    for [user_msg, ai_msg] in chat_history:
        history.add_user_message(user_msg)
        history.add_ai_message(ai_msg)

    cached_result = search_cached_answer(message)
    if cached_result.get("found"):
        bot_message = cached_result["answer"]
        print(f"キャッシュヒット (応答時間: {time.time() - start_time:.3f}秒)")
    else:
        if index is None:
            index = get_index()
        prompt = f"質問: {message}\n専門的に回答してください。"
        bot_message = chat(prompt, history, index)
        store_response_in_pinecone(message, bot_message)
        print("新規回答をPineconeに保存しました")

    chat_history.append((message, bot_message))
    if len(chat_history) > 3:
        chat_history.pop(0)
    return "", chat_history

# Gradio UI本体
with gr.Blocks(title="RAIDEN v1.320", css=".gradio-container {background-color:rgb(248,230,199)}") as app:
    gr.Markdown("# 歯科AIサポート - RAIDEN v1.320")

    with gr.Tabs():
        with gr.Tab("🦷 チャットボット"):
            chatbot = gr.Chatbot()
            msg = gr.Textbox(placeholder="歯科に関する質問を入力")
            clear = gr.ClearButton([msg, chatbot])
            msg.submit(respond, [msg, chatbot], [msg, chatbot])

        with gr.Tab("📊 欠損数チェッカー"):
            gr.Markdown("上下顎あわせて28本のうち、何本欠損しているかに応じた組み合わせ数を計算します。")
            slider = gr.Slider(0, 28, step=1, value=10, label="欠損歯の本数")
            output = gr.Textbox(label="結果", lines=2)
            slider.change(fn=calculate_combinations_28, inputs=slider, outputs=output)

# アプリ起動
app.launch(server_name="127.0.0.1", server_port=7860)