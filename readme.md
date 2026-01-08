# 👁️ OphthaKG: 基于 LightRAG 的眼科知识图谱构建项目

本项目利用 **LightRAG** 框架，通过处理眼科医学 Markdown 文档，自动化构建结构化的知识图谱。它支持混合检索（Hybrid Search），能够为复杂的眼科咨询提供深度关联的回答。

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

使用 `conda` 创建并激活隔离环境：

```bash
conda create -n LightRAG python=3.11 -y
conda activate LightRAG

```

### 2. 安装依赖

```bash
pip install lightrag-hku
pip install langchain==0.0.327

```

### 3. 配置 API Key

在项目根目录下找到`api_keys.py` 文件，并填入你的 API 密钥：

```python
# api_keys.py
CLOSEAI_API_KEY = "你的_API_KEY_在此"

```

### 4. 准备数据

将你的眼科医学指南或文献（`.md` 格式）放入以下目录：
`examples/project/markdowns/`

### 5. 启动构建

运行核心构建脚本，程序将自动扫描文档并生成知识图谱：

```bash
# 添加项目根目录到 pythonpath
export PYTHONPATH=/root/LightRAG:$PYTHONPATH
python openai_construct_medical_guide_db_from_md.py
# 或者后台运行
nohup python openai_construct_medical_guide_db_from_md &
```

---

## 📂 项目说明

* **输入**：`markdowns/` 文件夹下的所有 `.md` 文档。
* **输出**：在 `OphthaKG/` 目录下生成索引文件和 `graph_chunk_entity_relation.graphml`（可用 Gephi 打开查看图谱）。
* **断点续传**：脚本会自动跳过已处理的文件，若运行中断，重新执行即可，无需重复消耗 Token。

## 🔍 查询模式建议

| 模式 | 描述 |
| --- | --- |
| **Naive** | 基础向量检索。 |
| **Local** | 针对实体的邻居节点进行检索，适合查询症状。 |
| **Global** | 从全局语义总结，适合回答预后、综述类问题。 |
| **Hybrid** | **推荐模式**。结合图谱与向量，提供最精准的眼科医学分析。 |

---

### ⚠️ 注意事项

1. **API 额度**：构建过程会调用 LLM 进行实体和关系提取，请确保 API 余额充足。
2. **编码格式**：请确保所有 Markdown 文件均为 `UTF-8` 编码。