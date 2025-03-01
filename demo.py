import os
import ast
import sys
import pdb
import time
import json
import base64
import functools
import traceback
import shutil
from pprint import pprint

import sqlparse
import numpy as np
import pandas as pd
import gradio as gr
from groq import Groq
import matplotlib.pyplot as plt
from jigsawstack import JigsawStack
from sqlalchemy import create_engine
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv, find_dotenv
# Adapted from https://www.gradio.app/docs/gradio/multimodaltextbox#demos

def debug_on_error(func):
    """
    Decorator to start pdb post-mortem debugging on function exception.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            print(f"Exception in {func.__name__}: {e}")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            pdb.post_mortem(exc_traceback)
    return wrapper

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

    return history, gr.MultimodalTextbox(value=None, interactive=False)

def stream_response(history: list):
    print('stream_response')
    global data_analytics_agent

    # Generate response
    user_query = history[-1]['content']

    # Update bot response
    sql_query, result_df, plot_code, plot_fig = data_analytics_agent.inference_end2end(user_query)
    response_text = "Some response_text"
    history.append(
        {"role": "assistant", "content": response_text}
    )

    return history, gr.MultimodalTextbox(value=None, interactive=True), sql_query, result_df, plot_code, plot_fig

def debug_plot():
    # Generate sample data: x values and y values (for example, a quadratic function)
    x = np.arange(10)
    y = x ** 2

    # Create a figure and axis
    fig, ax = plt.subplots()

    # Plot the data as a simple line plot
    ax.plot(x, y)

    # Optional: add labels and title
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_title("Simple Line Plot")
    
    return fig

def debugger_here(chatbot, chat_input):
    text2sql, pandas_dataframe, visualisation_code, visualisation_code = None, None, None, None
    text2sql = """SELECT * FROM some_table WHERE date=2025"""
    pandas_dataframe = pd.DataFrame({ 'text': ['123', '456'], 'number': [123, 456], })
    
    if True: # plt locally
        visualisation_code = """def debug_plot():
            # Generate sample data: x values and y values (for example, a quadratic function)
            x = np.arange(10)
            y = x ** 2

            # Create a figure and axis
            fig, ax = plt.subplots()

            # Plot the data as a simple line plot
            ax.plot(x, y)

            # Optional: add labels and title
            ax.set_xlabel("X-axis")
            ax.set_ylabel("Y-axis")
            ax.set_title("Simple Line Plot")
            
            return fig
        """.strip()
        visualisation_plot = debug_plot()
        visualisation_plot.savefig('tmp.png')
        visualisation_plot = 'tmp.png'

    if False: # plt in e2b
        visualisation_code, visualisation_plot = data_analytics_agent.perform_visualisation(pandas_dataframe, "plot the text and number")
        with open('tmp.png', "wb") as f: f.write(base64.b64decode(visualisation_plot.png))
        visualisation_plot = 'tmp.png'
    return chatbot, chat_input, text2sql, pandas_dataframe, visualisation_code, visualisation_plot


DEFAULT_PROMPTS = {
    1: "I want to find out how D0001 and R0001 perform across outlets 1 to 3. Please output the results in a table where column headers are outlet names and row headers are product names",
    2: "I want to find out what percentage of my total sales come from warehouse sales",
    3: "Please track all invoices by location and create a bar chart where x axis is outlet or warehouse name and y axis is sales amount",
}

class DataAnalyticsAgent():
    def __init__(self):
        # Clients
        self.prepare_API()
        # Text2SQL
        self.sql_engine, self.sql_schema = self.prepare_SQL_data()
        self.text2sql_fewshots_lst = self.prepare_few_shot_Text2SQL()
        # Visualisation

    # Set up
    def prepare_API(self):
        self.jigsawstack = JigsawStack(
            api_key = os.getenv("JIGSAWSTACK_API")
        )
        self.client = Groq(
            api_key = os.getenv("GROQ_API_KEY")
        )
        self.sbx = Sandbox(
            api_key = os.getenv('E2B_API_KEY'),
            request_timeout=3_600,
        )

    # Data
    def prepare_SQL_data(self):
        # Load csv
        product_table_df = pd.read_csv('data/tables/Product Table.csv')
        invoice_table_df = pd.read_csv('data/tables/Invoice Table.csv')
        invoice_item_df = pd.read_csv('data/tables/Invoice Item.csv')
        outlet_df = pd.read_csv('data/tables/Outlet Table.csv')
        warehouse_df = pd.read_csv('data/tables/Warehouse Table.csv')
        address_df = pd.read_csv('data/tables/Address Table.csv')

        # Init sqlite
        file_path = "my_database.db"
        if os.path.exists(file_path):
            shutil.rmtree(file_path, ignore_errors=True)
            print(f"Removed: {file_path}")
        else:
            print(f"File not found: {file_path}")
        sql_engine = create_engine('sqlite:///my_database.db')

        # convert pandas dataframe to sqlite
        product_table_df.to_sql('datachat_product', sql_engine, index=False, if_exists='replace')
        invoice_table_df.to_sql('datachat_invoice', sql_engine, index=False, if_exists='replace')
        invoice_item_df.to_sql('datachat_invoiceitem', sql_engine, index=False, if_exists='replace')
        outlet_df.to_sql('datachat_outlet', sql_engine, index=False, if_exists='replace')
        warehouse_df.to_sql('datachat_warehouse', sql_engine, index=False, if_exists='replace')
        address_df.to_sql('datachat_address', sql_engine, index=False, if_exists='replace')

        # Prepare schema for Text2SQL
        schemas = {
            'datachat_product': pd.io.sql.get_schema(product_table_df, 'datachat_product', con=sql_engine),
            'datachat_invoice': pd.io.sql.get_schema(invoice_table_df, 'datachat_invoice', con=sql_engine),
            'datachat_invoiceitem': pd.io.sql.get_schema(invoice_item_df, 'datachat_invoiceitem', con=sql_engine),
            'datachat_outlet': pd.io.sql.get_schema(outlet_df, 'datachat_outlet', con=sql_engine),
            'datachat_warehouse': pd.io.sql.get_schema(warehouse_df, 'datachat_warehouse', con=sql_engine),
            'datachat_address': pd.io.sql.get_schema(address_df, 'datachat_address', con=sql_engine),
        }
        sql_schema = "-- DataChat Database Schema\n\n"
        for table, schema in schemas.items():
            cleaned_schema = schema.strip().rstrip(";")
            sql_schema += f"-- Table: {table}\n{cleaned_schema};\n\n"
        # To-Do add foreign keys to link them

        return sql_engine, sql_schema

    # Visualisation
    def inference_should_visualize(self, user_query):
        messages_visualisation = [
            {"role": "system", "content": "Validate whether the user requires visualisation in the task. If only table output is required, reply false. If matplotlib is required to show some plots, reply true."},
            {"role": "user", "content": "I want to find out how D0001 and T0001 perform across outlets 1 to 2. Please output the results in a table where column headers are outlet names and row headers are product names"},
            {"role": "assistant", "content": json.dumps({ "require matplotlib" : False })},
            {"role": "user", "content": "Please track all invoices by location and create a bar chart in excel where x axis is outlet or warehouse name and y axis is sales amount"},
            {"role": "assistant", "content": json.dumps({ "require matplotlib" : True })},
            {"role": "user", "content": "I want to find out what percentage of my total sales come from outlet sales"},
            {"role": "assistant", "content": json.dumps({ "require matplotlib" : False })},
            {"role": "user", "content": None},
        ]
        messages_visualisation[-1]['content'] = user_query

        response = self.client.chat.completions.create(
            model = "qwen-2.5-coder-32b",
            messages = messages_visualisation
        )

        require_visualisation_dict = json.loads(response.choices[0].message.content)
        return require_visualisation_dict['require matplotlib']

    def perform_visualisation(self, result_df, user_query):
        python_template = """
        ```python
        def function_v1(insert arguments here):
            # Insert code here
        ```
        """
        SYSTEM_PROMPT = f"""
        You are a Python data scientist. 
        Use this template:
        
        {python_template}
        
        Do not use xlsxwriter
        Use matplotlib
        """.strip()
        
        ### groq(qwen-2.5-coder-32b)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"{result_df}\n"
                "Given the above results\n"
                f"{user_query}"
            )},
        ]
        print(messages[-1]['content'])
        
        # Get code from Groq
        response = self.client.chat.completions.create(
            model = "qwen-2.5-coder-32b",
            messages = messages
        )
        # Extract and run the code
        code = response.choices[0].message.content
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        print(code)
        
        ### e2b - Eecute visualisation code
        sbx = Sandbox(
            api_key = os.getenv('E2B_API_KEY'),
            request_timeout = 3_600,
        )
        
        print("\nExecuting code in sandbox...")
        execution = sbx.run_code(code)
        pprint(execution)
        
        if len(execution.logs.stdout):
            print(execution.logs.stdout[0])
            
        if len(execution.results):
            execution.results[0]
        
        return code, execution.results[0]

    # Text2SQL
    def prepare_few_shot_Text2SQL(self):
        user_query_v1 = (
            "I want to find out how D0001 and T0001 perform across outlets 1 to 2. "
            "Please output the results in a table where column headers are outlet names and row headers are product names"
        )
        expected_response_v1 = """
            SELECT 
                p.product_code,
                SUM(CASE WHEN o.name = "Outlet 1" THEN ii.line_total ELSE 0 END) AS "Outlet 1" ,
                SUM(CASE WHEN o.name = "Outlet 2" THEN ii.line_total ELSE 0 END) AS "Outlet 2"
            FROM datachat_outlet o
                JOIN datachat_invoice i ON i.origin_address_id = o.address_id
                    JOIN datachat_invoiceitem ii ON ii.invoice_id = i.invoice_id
                        JOIN datachat_product p ON p.id = ii.product_id
            WHERE p.product_code IN ('D0001', 'T0001')
            GROUP BY p.product_code;
        """.replace("\n            ", '\n').strip()

        user_query_v2 = "I want to find out what percentage of my total sales come from outlet sales"
        expected_response_v2 = """
            SELECT 
            (SUM(i.total) * 100.0 / (SELECT SUM(total) FROM datachat_invoice)) AS outlet_sales_percentage
            FROM datachat_invoice i
            JOIN datachat_outlet w 
                ON i.origin_address_id = w.address_id
            WHERE i.origin_address_type = 1;
        """.replace("\n            ", '\n').strip()

        fewshot_examples_lst = [
            user_query_v1, expected_response_v1,
            user_query_v2, expected_response_v2,
        ]
        return fewshot_examples_lst

    def inference_Text2SQL(self, user_query, verbose=False):
        if verbose:
            print(sql_schema)
        
        user_query_fewshot = '\n'.join(self.text2sql_fewshots_lst + [user_query])
        
        params = {
            "prompt": user_query_fewshot,
            "sql_schema": self.sql_schema,
            'database': 'sqlite',
        }
        result = self.jigsawstack.text_to_sql(params)
        
        sql_query = result['sql']
        sql_query = sqlparse.format(sql_query, reindent=True, keyword_case='upper')
        return sql_query

    # End2End
    def inference_end2end(self, user_query, verbose=True):
        if verbose:
            print(f"user_query = {green_c}{user_query}{NC}")

        sql_query = self.inference_Text2SQL(user_query)
        if verbose:
            print(f"sql_query = \n{green_c}{sql_query}{NC}")

        result_df = pd.read_sql_query(sql_query, self.sql_engine)
        if verbose:
            print(f"result_df = \n{green_c}{result_df}{NC}")

        should_visualize = self.inference_should_visualize(user_query)
        if verbose:
            print(f"should_visualize = \n{green_c}{should_visualize}{NC}")

        plot_code, plot_fig = "", None
        if should_visualize:
            plot_code, plot_fig = self.perform_visualisation(result_df, user_query)
            # plot_fig = plot_fig.png
            with open('tmp.png', "wb") as f: f.write(base64.b64decode(plot_fig.png))
            plot_fig = 'tmp.png'

        if verbose:
            print(f"plot_code = \n{green_c}{plot_code}{NC}")
            print(f"plot_fig = \n{green_c}{plot_fig}{NC}")

        return sql_query, result_df, plot_code, plot_fig
global data_analytics_agent

# main
@debug_on_error
def main():
    # Set up gradio
    with gr.Blocks() as demo:
        gr.Markdown("Text2SQL & Code-Generated Visualisation")
        
        with gr.Row():
            with gr.Column(scale=1):
                # Interface
                ## Chat history
                chatbot = gr.Chatbot(
                    elem_id = "chatbot", 
                    bubble_full_width = False, 
                    type = "messages",
                )
                
                # Default Prompt Options: using a Radio widget for simplicity
                default_prompt_radio = gr.Radio(
                    label="Select a Default Prompt",
                    choices=list(DEFAULT_PROMPTS.values()),
                    value=list(DEFAULT_PROMPTS.values())[0]
                )
                
                ## Input / Response
                chat_input = gr.MultimodalTextbox(
                    interactive = True,
                    file_count = "multiple",
                    placeholder = "Enter message or upload file...",
                    show_label = False,
                    sources = ["microphone", "upload"],
                    value = "",
                )
                
                # When a default prompt is selected, update the chat input
                default_prompt_radio.change(
                    fn=lambda prompt: prompt,
                    inputs=default_prompt_radio,
                    outputs=chat_input
                )
                
                ## Debug
                debug_button = gr.Button("Debug")
            
            with gr.Column(scale=1):
                text2sql_output = gr.Textbox(
                    label = "Text2SQL result",
                    interactive = True
                )
                pandas_dataframe_output = gr.Dataframe(
                    label = "Data retrieved",
                    interactive = False
                )
                visualisation_code_output = gr.Code(
                    label = "Code Output",
                    language = "python",
                    interactive = True,
                )
                # visualisation_plot_output = gr.Plot(
                #     label = "Visualisation Output",
                #     format = "png",
                # )
                visualisation_plot_output = gr.Image(
                    label = "Visualisation Output",
                )

        # Actions
        if True:
            ## Input
            chat_msg = chat_input.submit(
                fn = process_input,
                inputs = [chatbot, chat_input],
                outputs = [chatbot, chat_input]
            )
            ## Response
            bot_msg = chat_msg.then(
                    fn = stream_response,
                    inputs = [chatbot],
                    outputs = [
                        chatbot, chat_input,
                        text2sql_output, pandas_dataframe_output, visualisation_code_output, visualisation_plot_output
                    ],
            )
            ## Debug
            debug_button.click(
                fn = debugger_here,
                inputs = [chatbot, chat_input],
                outputs = [
                        chatbot, chat_input,
                        text2sql_output, pandas_dataframe_output, visualisation_code_output, visualisation_plot_output
                    ]
            )

    demo.launch()


# ------------------------------------------------------------
if True:
    # Reset to normal (No Color)
    NC = "\033[0m"

    # Standard colors (non-bright)
    black_c   = "\033[30m"
    red_c     = "\033[31m"
    green_c   = "\033[32m"
    yellow_c  = "\033[33m"
    blue_c    = "\033[34m"
    magenta_c = "\033[35m"
    cyan_c    = "\033[36m"
    white_c   = "\033[37m"
    # Brighter variants:
    bright_black_c   = "\033[90m"
    bright_red_c     = "\033[91m"
    bright_green_c   = "\033[92m"
    bright_yellow_c  = "\033[93m"
    bright_blue_c    = "\033[94m"
    bright_magenta_c = "\033[95m"
    bright_cyan_c    = "\033[96m"
    bright_white_c   = "\033[97m"

    print(f'{black_c  }This is black   {NC}')
    print(f'{red_c    }This is red     {NC}')
    print(f'{green_c  }This is green   {NC}')
    print(f'{yellow_c }This is yellow  {NC}')
    print(f'{blue_c   }This is blue    {NC}')
    print(f'{magenta_c}This is magenta {NC}')
    print(f'{cyan_c   }This is cyan    {NC}')
    print(f'{white_c  }This is white   {NC}')
    print(f'{bright_black_c  }This is bright_black   {NC}')
    print(f'{bright_red_c    }This is bright_red     {NC}')
    print(f'{bright_green_c  }This is bright_green   {NC}')
    print(f'{bright_yellow_c }This is bright_yellow  {NC}')
    print(f'{bright_blue_c   }This is bright_blue    {NC}')
    print(f'{bright_magenta_c}This is bright_magenta {NC}')
    print(f'{bright_cyan_c   }This is bright_cyan    {NC}')
    print(f'{bright_white_c  }This is bright_white   {NC}')

    print()

if __name__ == "__main__":
    load_dotenv(find_dotenv())
    assert not os.getenv("JIGSAWSTACK_API") is None
    assert not os.getenv("GROQ_API_KEY") is None
    assert not os.getenv("E2B_API_KEY") is None
    data_analytics_agent = DataAnalyticsAgent()
    main()
