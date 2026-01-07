import os
import asyncio
import logging
import logging.config
from pinecone import Pinecone
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import logger, set_verbose_debug

from lightrag.rerank import custom_rerank, RerankModel, jina_rerank
from api_keys import *

# logging.basicConfig(level=logging.DEBUG)
# WORKING_DIR = "./medical_guide_db_from_md_v5-debug"
WORKING_DIR = "./medical_guide_db_from_md_v8-debug-only-title-subsection"
# WORKING_DIR = "./medical_guide_db_from_md_v3"
query = "What is the long-term prognosis for my left eye primary acute angle-closure glaucoma?"

def configure_logging():
    """Configure logging for the application"""

    # Reset any existing handlers to ensure clean configuration
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "lightrag"]:
        logger_instance = logging.getLogger(logger_name)
        logger_instance.handlers = []
        logger_instance.filters = []

    # Get log directory path from environment variable or use current directory
    log_dir = os.getenv("LOG_DIR", os.getcwd())
    log_file_path = os.path.abspath(os.path.join(log_dir, "lightrag_demo.log"))

    print(f"\nLightRAG demo log file: {log_file_path}\n")
    os.makedirs(os.path.dirname(log_dir), exist_ok=True)

    # Get log file max size and backup count from environment variables
    log_max_bytes = int(os.getenv("LOG_MAX_BYTES", 10485760))  # Default 10MB
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))  # Default 5 backups

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(levelname)s: %(message)s",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
                "file": {
                    "formatter": "detailed",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file_path,
                    "maxBytes": log_max_bytes,
                    "backupCount": log_backup_count,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "lightrag": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    )

    # Set the logger level to INFO
    logger.setLevel(logging.DEBUG)  # INFO
    # Enable verbose debug if needed
    set_verbose_debug(os.getenv("VERBOSE_DEBUG", "false").lower() == "true")


if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


async def my_rerank_func(query: str, documents: list,
                         top_n: int = None, # will not take effect even set here
                         **kwargs):
    """Custom rerank function using Pinecone"""
    pc = Pinecone(
        api_key='pcsk_2QfAFP_MVT7YKz9DG4E4Q5dQzpEBzfH8JYrKFeaGfvr5WeqVQBQ76F6vipWn3AsGxcF8uA',
        environment="gcp-starter"
    )
    try:
        results = pc.inference.rerank(
            model="cohere-rerank-3.5",
            query=query,
            rank_fields=["content"],
            documents=documents,
            top_n=top_n,
            return_documents=True
        )
        # return [r.document.content for r in results.data]
        return documents if not documents else [
            {k: getattr(r.document, k, None) for k in documents[0].keys()}
            for r in results.data
        ]
    except Exception as e:
        print(f"Pinecone rerank 失败: {e}")
        # 降级到原始文档顺序
        return documents  # [:top_n]

#
# async def my_rerank_func(query: str, documents: list,
#                          top_n: int = None,
#                          **kwargs):
#     """Custom rerank function with all settings included"""
#     return await custom_rerank(
#         query=query,
#         documents=documents,
#         # model="BAAI/bge-reranker-v2-m3",
#         # base_url="https://api.your-rerank-provider.com/v1/rerank",
#         # api_key="your_rerank_api_key_here",
#         model="jina-reranker-v2-base-multilingual",
#         base_url="https://api.jina.ai/v1/rerank",
#         api_key="jina_7bfcde93c64b47bbb7e65bbd918e65feIPGzLuesTT5PJ6I1nS5y7dbIfGdY",
#         top_n=top_n,  # this value did not take effect
#         **kwargs,
#     )

async def initialize_rag():
    # rerank_model = RerankModel(
    #     rerank_func=jina_rerank,
    #     kwargs={
    #         "model": "jina-reranker-v2-base-multilingual",  # BAAI/bge-reranker-v2-m3
    #         "api_key": "jina_7bfcde93c64b47bbb7e65bbd918e65feIPGzLuesTT5PJ6I1nS5y7dbIfGdY",
    #         "base_url": "https://api.jina.ai/v1/rerank",
    #         "top_n":5
    #     }
    # )
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
        chunk_token_size=1000,
        chunk_overlap_token_size=100,

        # Rerank Configuration - provide the rerank function
        rerank_model_func=my_rerank_func,
        # rerank_model_func=rerank_model.rerank,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag


async def main():
    # Check if OPENAI_API_KEY environment variable exists
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "Error: OPENAI_API_KEY environment variable is not set. Please set this variable before running the program."
        )
        print("You can set the environment variable by running:")
        print("  export OPENAI_API_KEY='your-openai-api-key'")
        return  # Exit the async function
    try:
        # # Clear old data files
        # files_to_delete = [
        #     "graph_chunk_entity_relation.graphml",
        #     "kv_store_doc_status.json",
        #     "kv_store_full_docs.json",
        #     "kv_store_text_chunks.json",
        #     "vdb_chunks.json",
        #     "vdb_entities.json",
        #     "vdb_relationships.json",
        # ]
        #
        # for file in files_to_delete:
        #     file_path = os.path.join(WORKING_DIR, file)
        #     if os.path.exists(file_path):
        #         os.remove(file_path)
        #         print(f"Deleting old file:: {file_path}")

        # Initialize RAG instance
        rag = await initialize_rag()

        # Test embedding function
        test_text = ["This is a test string for embedding."]
        embedding = await rag.embedding_func(test_text)
        embedding_dim = embedding.shape[1]
        print("\n=======================")
        print("Test embedding function")
        print("========================")
        print(f"Test dict: {test_text}")
        print(f"Detected embedding dimension: {embedding_dim}\n\n")

        # # # # # with open("./book.txt", "r", encoding="utf-8") as f:
        # # # # #     await rag.ainsert(f.read())
        # with open("./Primary Angle-Closure Disease PPP.md", "r", encoding="utf-8") as f:
        #     await rag.ainsert(
        #         f.read(),
        #         # split_by_character=["\n## ", "\n### ", "\n#### ","\n\n", "\n", " ", ""],
        #         ids='Primary Angle-Closure Disease PPP',
        #         file_paths=["./Primary Angle-Closure Disease PPP.md"],
        #     )
        # md_file_dir = 'markdown_glaucoma_mini'
        # md_files = [f for f in os.listdir(md_file_dir) if f.endswith('.md')][::-1]
        #
        # # tasks = []
        # for k, filename in enumerate(md_files):
        #     print(f"\n\n\n\n\n\n--- Analyzing: {k}/{len(md_files)} file, {filename} ---\n\n\n\n\n\n\n\n\n\n\n\n")
        #     filepath = os.path.join(md_file_dir, filename)
        #     with open(filepath, "r", encoding="utf-8") as f:
        #         await rag.ainsert(
        #             f.read(),
        #             ids=os.path.basename(filename).replace('.md', ''),
        #             file_paths=filepath,
        #         )
        # # Perform naive search
        # print("\n=====================")
        # print("Query mode: naive")
        # # print("=====================")
        # result = await rag.aquery(
        #         query, param=QueryParam(
        #             mode="naive",
        #             enable_rerank=True, # Explicitly enable rerank
        #             rerank_top_n=10,  # Number of top documents to rerank and return
        #             only_need_retrieved_context_list=True,
        #             chunk_top_k=20,
        #         )
        #         # query, param=QueryParam(mode="naive", only_need_context=True)
        #     )
        # print(result)

        # # Perform local search
        # print("\n=====================")
        # print("Query mode: local")
        # print("=====================")
        # print(
        #     await rag.aquery(
        #         # query, param=QueryParam(mode="local", only_need_context=True),
        #         query, param=QueryParam(mode="local")
        #     )
        # )
        #
        # Perform global search
        print("\n=====================")
        print("Query mode: global")
        print("=====================")
        result = await rag.aquery(
                query,
                # param=QueryParam(mode="global", only_need_context=True),
                param=QueryParam(
                    mode="global",
                    only_need_context=True,
                    # only_need_retrieved_context_list=True,
                    enable_rerank=True, # Explicitly enable rerank
                    rerank_top_n=10,  # Number of top documents to rerank and return
                ),
        )
        print(result)

        # Perform hybrid search
        print("\n=====================")
        print("Query mode: hybrid")
        print("=====================")
        print(
            await rag.aquery(
                query,
                param=QueryParam(
                    mode="hybrid",
                    enable_rerank=True,  # Explicitly enable rerank
                    rerank_top_n=20,  # Number of top documents to rerank and return
                ),  # only_need_context=True
            )
        )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if rag:
            await rag.finalize_storages()


if __name__ == "__main__":
    # Configure logging before running the main function
    configure_logging()
    asyncio.run(main())
    print("\nDone!")
