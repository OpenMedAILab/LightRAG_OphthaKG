import os
import asyncio
import logging
import logging.config
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import logger, set_verbose_debug
import api_keys

# ================= 配置区域 =================
WORKING_DIR = "./OphthaKG"
MD_FILE_DIR = './markdowns'
# 记录已处理文件，防止崩溃后重头开始
PROCESSED_LOG = os.path.join(WORKING_DIR, "processed_files.txt")
# 并发数控制：根据你的 API 额度调整。gpt-4o-mini 建议 3-5，防止 Rate Limit
MAX_CONCURRENT_TASKS = 1


# ================= Logging 配置 =================
def configure_logging():
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "lightrag"]:
        logger_instance = logging.getLogger(logger_name)
        logger_instance.handlers = []

    log_file_path = os.path.join(WORKING_DIR, "lightrag_build.log")

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
            "simple": {"format": "%(levelname)s: %(message)s"},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "simple"},
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_file_path,
                "maxBytes": 10485760,
                "backupCount": 5,
                "encoding": "utf-8",
                "formatter": "detailed"
            },
        },
        "loggers": {
            "lightrag": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        }
    })
    set_verbose_debug(False)


# ================= 辅助函数 =================
def get_processed_files():
    """读取已经成功索引的文件列表"""
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()


def mark_as_processed(filename):
    """记录成功处理的文件"""
    with open(PROCESSED_LOG, "a", encoding="utf-8") as f:
        f.write(f"{filename}\n")


# ================= 核心处理逻辑 =================
async def process_file(semaphore, rag, filename):
    """带并发控制的单个文件导入"""
    async with semaphore:
        filepath = os.path.join(MD_FILE_DIR, filename)
        try:
            print(f"正在分析: {filename}...")
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return

                # 调用异步插入
                await rag.ainsert(
                    content,
                    ids=filename.replace('.md', ''),
                    file_paths=filepath,
                )

            mark_as_processed(filename)
            print(f"成功导入: {filename}")
        except Exception as e:
            logging.error(f"处理文件 {filename} 时发生错误: {str(e)}")


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag


async def main():
    if not os.path.exists(WORKING_DIR):
        os.makedirs(WORKING_DIR)

    configure_logging()

    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请先设置 OPENAI_API_KEY 环境变量。")
        return

    # 初始化 RAG
    rag = await initialize_rag()

    # 扫描文件夹
    if not os.path.exists(MD_FILE_DIR):
        print(f"错误: 找不到目录 {MD_FILE_DIR}")
        return

    all_files = [f for f in os.listdir(MD_FILE_DIR) if f.endswith('.md')]
    processed_files = get_processed_files()
    files_to_process = [f for f in all_files if f not in processed_files]

    print(
        f"\n项目状态: 共 {len(all_files)} 个文件, 已处理 {len(processed_files)} 个, 剩余 {len(files_to_process)} 个待处理。")

    # 批量异步处理（带信号量控制流量）
    if files_to_process:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
        tasks = [process_file(semaphore, rag, f) for f in files_to_process]
        await asyncio.gather(*tasks)
        print("\n所有文件索引完成！")
    else:
        print("\n没有新文件需要处理。")

    # 测试查询
    test_query = "What is the long-term prognosis for my left eye primary acute angle-closure glaucoma?"
    print(f"\n执行测试查询: {test_query}")
    print("-" * 30)

    # 使用 Hybrid 模式，这在眼科这种专业领域效果最好
    result = await rag.aquery(test_query, param=QueryParam(mode="hybrid"))
    print(f"\nRAG 回答:\n{result}")

    await rag.finalize_storages()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户手动停止。已保存当前进度。")
    except Exception as e:
        print(f"\n运行出错: {e}")
