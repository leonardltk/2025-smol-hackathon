import ast
import pdb
import time
from pprint import pprint
import gradio as gr
# Adapted from https://www.gradio.app/docs/gradio/multimodaltextbox#demos

# Gradio functions
def process_input(history, message):
    print('process_input')

    for x in message["files"]:
        history.append(
            {"role": "user", "content": {"path": x}}
        )
    if message["text"] is not None:
        history.append(
            {"role": "user", "content": message["text"]}
        )

    canvas_output = "Computing..."

    return history, gr.MultimodalTextbox(value=None, interactive=False), canvas_output

def stream_response(history: list, output_input: str, ):
    print('stream_response')

    # Generate response
    user_query = history[-1]['content']
    response_dict = RAGcipe_langgraph.make_question(
        user_query,
        output_input,
    )
    response_dict_history = response_dict['history']
    response_dict_event = response_dict['event']

    # Parse response
    response_text = ""
    canvas_output = ""
    output_page_output = ""

    # Update bot response
    response_text = "Some output"
    history.append(
        {"role": "assistant", "content": response_text}
    )

    return history, gr.MultimodalTextbox(value=None, interactive=True), canvas_output, output_page_output

def debugger_here():
    print('debugger_here')
    pdb.set_trace()
    return


# main
def main():
    with gr.Blocks() as demo:
        gr.Markdown("# xxx v2")

        with gr.Row():
            with gr.Column(scale=1):
                # Interface
                ## Chat history
                chatbot = gr.Chatbot(
                    elem_id = "chatbot", 
                    bubble_full_width = False, 
                    type = "messages",
                )
                ## Input / Response
                chat_input = gr.MultimodalTextbox(
                    interactive = True,
                    file_count = "multiple",
                    placeholder = "Enter message or upload file...",
                    show_label = False,
                    sources = ["microphone", "upload"],
                    value = "Give me a recipe for pasta",
                )
                ## Debug
                debug_button = gr.Button("Debug")

            with gr.Column(scale=1):
                ranked_canvas = gr.Textbox(
                    label="Ranked Results",
                    interactive=False
                )
                output_page = gr.Textbox(
                    label="Recipe Details",
                    interactive = True,
                )

        # Actions
        if True:
            ## Input
            chat_msg = chat_input.submit(
                fn = process_input,
                inputs = [chatbot, chat_input],
                outputs = [chatbot, chat_input, ranked_canvas]
            )
            ## Response
            bot_msg = chat_msg.then(
                    fn = stream_response,
                    inputs = [chatbot, output_page],
                    outputs = [chatbot, chat_input, ranked_canvas, output_page],
                api_name="bot_response",
            )
            ## Debug
            debug_button.click(
                fn=debugger_here,
                inputs=[],
                outputs=[]
            )

    demo.launch()


if __name__ == "__main__":
    main()
