from main import run_dynamic_recommender
from main import show_read_books
import gradio as gr

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            category_input = gr.Textbox(label="Enter a book that you read", placeholder="e.g., Dune, Sapiens, The Hobbit")
            submit_button = gr.Button("Get Recommendations!")
        with gr.Column():
            output_display = gr.Textbox(label="Recommended Books", lines=10)

    submit_button.click(fn=run_dynamic_recommender, inputs=category_input, outputs=output_display)

    with gr.Row():
        with gr.Column():
            show_button = gr.Button("Show Read Books")
        with gr.Column():
            save_output = gr.DataFrame(label="Books You Have Read", interactive=False)
            clear_button = gr.Button("Clear Read Books")

    show_button.click(fn=show_read_books, inputs=None, outputs=save_output)

if __name__ == "__main__":
    demo.launch(share=True)
