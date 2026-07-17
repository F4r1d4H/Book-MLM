from main import run_dynamic_recommender, show_read_books, show_read_later, save_to_read_later, clear_saved_lists
import gradio as gr
import pandas as pd


def get_read_books_table():
    read_books = show_read_books()
    if read_books.empty:
        return pd.DataFrame(columns=["authors", "genre", "title", "owned", "rating"])
    return read_books.reindex(columns=["authors", "genre", "title", "owned", "rating"]).fillna("")

def get_read_later_table():
    read_later = show_read_later()
    if read_later.empty:
        return pd.DataFrame(columns=["authors", "genre", "title"])
    return read_later.reindex(columns=["authors", "genre", "title"]).fillna("")

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            gr.Markdown("## 📖 Book Recommender System")
            gr.Markdown("Enter a book you've read, indicate if you own it, and provide a rating. Click 'Get Recommendations!' to receive personalized book suggestions and then adjust your reading list.")
            category_input = gr.Textbox(label="Enter a book that you read", placeholder="e.g., Dune, Sapiens, The Hobbit")
            own_book_checkbox = gr.Checkbox(label="Do you own this book?", value=False)
            rating = gr.Radio(
                choices=["0", "⭐ 1", "⭐⭐ 2", "⭐⭐⭐ 3", "⭐⭐⭐⭐ 4", "⭐⭐⭐⭐⭐ 5"], 
                label="Select a rating"
            )
            submit_button = gr.Button("Get Recommendations!", variant="primary")
            
    # --- FIX: Wrapped output_display inside an explicit layout row ---
    with gr.Row():
        with gr.Column():
            output_display = gr.DataFrame(label="Recommended Books", interactive=False)
    
    # --- Save to Read Later Interactive Row ---
    with gr.Row():
        with gr.Column():
            read_later_dropdown = gr.Dropdown(choices=[], label="Select a book to save for later", interactive=True)
            save_later_button = gr.Button("💾 Save Selected to Read Later", variant="secondary")

    with gr.Row():
        with gr.Column():
            save_output = gr.DataFrame(
                label="Books You Have Read",
                interactive=False,
                value=get_read_books_table(),
                headers=["authors", "genre", "title", "owned", "rating"],
                datatype=["str", "str", "str", "bool", "str"],
            )
        # --- Read Later Display Table ---
        with gr.Column():
            read_later_output = gr.DataFrame(
                label="Books to Read Later",
                interactive=False,
                value=get_read_later_table(),
                headers=["authors", "genre", "title"],
                datatype=["str", "str", "str"],
            )

    def on_submit(user_input, owns_book, book_rating):
        recommendations = run_dynamic_recommender(user_input, owned=owns_book, book_rating=book_rating)
        read_books = get_read_books_table()
        
        if not recommendations.empty and "Message" not in recommendations.columns:
            title_col = recommendations.columns[0] 
            choices = recommendations[title_col].tolist()
        else:
            choices = []
            
        return (
            recommendations, 
            read_books, 
            gr.Dropdown(choices=choices, value=choices[0] if choices else None, interactive=True)
        )

    submit_button.click(
        fn=on_submit,
        inputs=[category_input, own_book_checkbox, rating],
        outputs=[output_display, save_output, read_later_dropdown]
    )

    save_later_button.click(
        fn=save_to_read_later,
        inputs=[read_later_dropdown],
        outputs=[read_later_output]
    )

    with gr.Row():
        with gr.Column():
            show_button = gr.Button("Show Read Books", variant="primary")
        with gr.Column():
            show_later_btn = gr.Button("Show Read Later List", variant="primary")
            
    clear_button = gr.Button("Clear Read & Read Later Lists")

    show_button.click(fn=get_read_books_table, inputs=None, outputs=save_output)
    show_later_btn.click(fn=get_read_later_table, inputs=None, outputs=read_later_output)
    clear_button.click(fn=clear_saved_lists, inputs=None, outputs=[save_output, read_later_output])

if __name__ == "__main__":
    demo.launch(share=True)