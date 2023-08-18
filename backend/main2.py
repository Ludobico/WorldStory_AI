import asyncio
import os
from typing import AsyncIterable, Awaitable, Callable, Optional, Union, Any
from uuid import UUID

import uvicorn
# 스트리밍 output
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.callbacks.base import AsyncCallbackHandler
from pydantic import BaseModel

# LLM
from langchain.llms import LlamaCpp
from langchain import PromptTemplate, LLMChain
from langchain.callbacks.manager import CallbackManager

app = FastAPI()

template = """
Question : {question}

Answer : Let's work this out in a step by step way to be sure we habe the right answer.
"""

prompt = PromptTemplate(template=template, input_variables=["question"])

Sender = Callable[[Union[str, bytes]], Awaitable[None]]


class AsyncStreamCallbackHandler(AsyncCallbackHandler):
    def __init__(self, send: Sender):
        super().__init__()
        self.send = send

    async def on_llm_new_token(self, token: str, *, run_id: UUID, parent_run_id: UUID, **kwargs):
        await self.send(f"data : {0} \n\n".format(token))


async def send_message(message: str) -> AsyncIterable[str]:
    callback = AsyncIteratorCallbackHandler()
    callback_manager = CallbackManager([callback])

    llm = LlamaCpp(model_path="./Models/WizardLM-13B-1.0.ggmlv3.q4_0.bin",
                   callback_manager=callback_manager, verbose=True, streaming=True)
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    question = "What NFL team won the Super Bowl in the year Justin Bierber was born?"

    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        try:
            await fn
        except Exception as e:
            print("Caught exception : {0}".format(e))
        finally:
            event.set()
