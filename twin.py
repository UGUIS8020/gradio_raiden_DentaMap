import gradio as gr
import threading

# 1つ目のGradioアプリ（シンプルな挨拶）
def greet1(name):
    return "こんにちは " + name + "さん!"

demo1 = gr.Interface(fn=greet1, inputs="text", outputs="text")

# 2つ目のGradioアプリ（スライダー付き挨拶）
def greet2(name, intensity):
    return "Hello, " + name + "!" * int(intensity)

demo2 = gr.Interface(
    fn=greet2,
    inputs=["text", "slider"],
    outputs=["text"],
)

# スレッドで1つ目のアプリを起動
def run_app1():
    demo1.launch(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True)

# スレッドを開始
thread = threading.Thread(target=run_app1)
thread.daemon = True
thread.start()

# メインスレッドで2つ目のアプリを起動
demo2.launch(server_name="127.0.0.1", server_port=7861, share=False, inbrowser=True)