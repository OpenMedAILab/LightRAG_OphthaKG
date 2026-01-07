
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
# WORKING_DIR = "./mule_test_construct_graph"
WORKING_DIR = "./medical_guide_db_from_md_parallel"

query = "What is the long-term prognosis for my left eye primary acute angle-closure glaucoma?"


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
        max_parallel_insert=8,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag

rag_test = asyncio.run(initialize_rag())

md_file_dir = 'medical_guide_markdown'
md_files = [f for f in os.listdir(md_file_dir) if f.endswith('.md')]

doc = []
texts = []
# tasks = []
for k, filename in enumerate(md_files):
    print(f"\n--- Analyzing: {k}/{len(md_files)} file, {filename} ---")
    filepath = os.path.join(md_file_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    texts.append(text)
    doc.append(filename.replace(".md", ""))



# rag_test.insert("文本1", )
# rag_test.insert("文本2", )
# rag_test.insert("文本1", )
#
rag_test.insert(texts)
#
# rag.insert(["文本1", "文本2",...])
#
# rag.insert(["文本3", "文本2",...])
