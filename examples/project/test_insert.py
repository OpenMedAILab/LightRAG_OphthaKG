
import os
import asyncio
import logging
import logging.config
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import logger, set_verbose_debug

from api_keys import *

# logging.basicConfig(level=logging.DEBUG)
WORKING_DIR = "./mule_test_construct_graph3"

query = "What is the long-term prognosis for my left eye primary acute angle-closure glaucoma?"


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

rag_test = asyncio.run(initialize_rag())

rag_test.insert("文本1", )
rag_test.insert("文本2", )
# rag_test.insert("文本1", )

# rag_test.insert(["文本1", "文本2",...])
#
# rag.insert(["文本1", "文本2",...])
#
# rag.insert(["文本3", "文本2",...])
