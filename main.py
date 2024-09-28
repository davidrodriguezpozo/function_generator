import os
import random
import re
from typing import Dict, List, Tuple

import httpx
import traceback
import openai
from bs4 import BeautifulSoup
from openai import OpenAI
import ast

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CHAT_MODEL = "gpt-4o"
MAX_TRIES = 10
llm = OpenAI(api_key=OPENAI_API_KEY)

_useragent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
]


def get_useragent():
    return random.choice(_useragent_list)


def search_method(url: str) -> Tuple[str, str, str]:
    """Search online for a query.

    Args:
        query (str): Query to search for.

    Returns:
        str: Search results.
    """
    r = httpx.get(
        url,
        headers={"User-Agent": get_useragent()},
    )
    parsed = BeautifulSoup(r.text, "html.parser")
    header = parsed.find(attrs=dict(id="page-header"))

    description = parsed.find(class_="ocpIntroduction")
    sections = parsed.find_all(class_="ocpSection")

    return (
        header.get_text(),
        description.get_text(),
        "\n".join([s.get_text() for s in sections]),
    )


def send_message(messages: List[Dict]) -> str:
    response = (
        llm.chat.completions.create(
            messages=messages,
            model=CHAT_MODEL,
        )
        .choices[0]
        .message.content
    )
    messages.append({"role": "assistant", "content": response})
    return response


def extract_script(response: str) -> str:
    pattern = r"```(\s*(python)\s*\n)?([\s\S]*?)```"

    m = re.search(pattern, response)
    if not m:
        return "I couldn't find a solution for this problem."

    return m.group(3)


# From https://medium.com/bitgrit-data-science-publication/openai-code-interpreter-ecda4ff5839c
def run(code: str):
    """Executes the given Python code and returns the result.

    Args:
        code: The Python code to execute.

    Returns:
        The result of the executed code.
    """
    tree = ast.parse(code)
    last_node = tree.body[-1] if tree.body else None

    # If the last node is an expression, modify the AST to capture the result
    if isinstance(last_node, ast.Expr):
        tgts = [ast.Name(id="_result", ctx=ast.Store())]
        assign = ast.Assign(targets=tgts, value=last_node.value)
        tree.body[-1] = ast.fix_missing_locations(assign)

    ns = {}
    exec(compile(tree, filename="<ast>", mode="exec"), ns)
    return ns.get("_result", None)


def execute_script(script: str) -> Tuple[str, str]:
    to_run = extract_script(script)
    print("To run: ")
    print(to_run)
    error = ""
    try:
        run(to_run)
    except Exception as e:
        error += f"An error occurred while running the provided code: {e}"
        error += traceback.format_exc()
        print("Error: ", error)

    return to_run, error


def _generate_method(method_name: str, description: str, extra: str) -> str:
    message = f"""
        Given the Microsoft Excel function {method_name}, with description: {description}, and the following extra information: {extra}.

Implement a method in Python using the polars package, that takes as argument as many pl.Expressions as arguments the function has, and returns a single Expression, being this the result of the operation.

Regardless of the number or arguments, the argument of the function should always be an expanded argument: *args

Moreover, using the example in "extra", create a test case for the function that asserts the result of the function with the expected result.

Return only the function definition and the test case - wrapped in a function called `test` (starting with def and ending with the last line of the function definition).

Then execute the test function. Bear in mind that the whole code will be run in an `exec` function, so make sure to import the necessary libraries and functions.
"""
    messages = [
        {"role": "user", "content": message},
    ]
    tries = 0
    response = send_message(messages)
    to_run, error = execute_script(response)

    while error and tries < MAX_TRIES:
        messages.append({"role": "user", "content": error})
        response = send_message(messages)
        to_run, error = execute_script(response)
        tries += 1

    if error:
        return "I couldn't find a solution for this problem."

    return to_run


def generate_method_from_url(url: str) -> str:
    method_name, description, extra = search_method(url)
    return _generate_method(method_name, description, extra)
