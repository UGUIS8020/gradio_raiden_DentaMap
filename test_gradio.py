from flask import Flask, render_template
import gradio as gr

app = Flask(__name__)

# Gradioインターフェースの作成
def greet(name):
    return f"Hello, {name}!"

gradio_interface = gr.Interface(fn=greet, inputs="text", outputs="text")

# Flaskルートの定義
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/gradio")
def gradio_ui():
    # GradioインターフェースをFlaskアプリに統合
    return gradio_interface.launch(share=True, inline=True)

if __name__ == "__main__":
    app.run(debug=True)