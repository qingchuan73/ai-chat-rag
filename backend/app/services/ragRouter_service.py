from services.llm_service import invoke


def should_use_knowledge(question: str, history=None, attachments=None, model_config=None) -> bool:
    if attachments:
        return True

    if not model_config:
        return False

    prompt = [
        {
            "role": "system",
            "content": """
            你是 RAG 意图路由器。
            请判断当前用户问题是否需要使用用户上传的知识库。
            只回答 yes 或 no。

            回答 yes 的情况：
            - 用户明确提到文档、文件、知识库、资料、附件、PDF、原文、页码、引用、来源。
            - 用户在询问、核对或分析最近上传/已上传资料里的内容。
            - 最近对话已经围绕知识库资料展开，当前问题是相关追问。

            回答 no 的情况：
            - 普通知识、常识、闲聊、代码、翻译、写作、动漫人物、影视角色、生活问题等。
            - 问题明显与用户上传资料无关。
            - 只是因为知识库里存在一些低相关词，不应回答 yes。

            不要依赖固定关键词，请根据用户真实意图和最近对话上下文判断。
            """
        },
        {
            "role": "user",
            "content": f"""
            最近对话：
            {history or []}

            当前问题：
            {question}
            """
        }
    ]

    try:
        result = invoke(
            messages=prompt,
            model_config=model_config
        )
        answer = result.content.strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False


def classify_rag_question_type(question: str, history=None, model_config=None) -> str:
    if not model_config:
        return "lookup"

    prompt = [
        {
            "role": "system",
            "content": """
            你负责判断一个知识库问题应该如何回答。
            只回答一个单词：
            - synthesis
            - lookup

            如果用户需要文档级、章节级、主题级、对比型、总结型、列表型、概览型或多要点回答，
            并且通常需要综合多个 chunk 或多个页面的信息，回答 synthesis。

            如果用户询问具体事实、原文、页码、来源、定义、要求、参数或窄范围细节，
            并且少量 chunk 就能回答，回答 lookup。

            请根据意图和最近对话判断，不要依赖固定关键词。
            """
        },
        {
            "role": "user",
            "content": f"""
            最近对话：
            {history or []}

            当前问题：
            {question}
            """
        }
    ]

    try:
        result = invoke(
            messages=prompt,
            model_config=model_config
        )
        answer = result.content.strip().lower()

        if answer.startswith("synthesis"):
            return "synthesis"

        return "lookup"
    except Exception:
        return "lookup"


def expand_rag_retrieval_queries(question: str, history=None, model_config=None) -> list[str]:
    if not model_config:
        return [question]

    prompt = [
        {
            "role": "system",
            "content": """
            你负责为知识库问题生成多路检索查询。
            请输出 3 到 5 条简短查询，每行一条。
            不要编号，不要回答问题。

            这些查询应该覆盖文档中可能分散出现的不同证据角度，
            例如目标、重点、背景、要求、实施路径、业务规划、约束条件和结论。

            保留用户主题和限制条件。
            不要添加用户问题或最近对话中不存在的事实。
            不要依赖固定关键词。
            """
        },
        {
            "role": "user",
            "content": f"""
            最近对话：
            {history or []}

            当前问题：
            {question}
            """
        }
    ]

    try:
        result = invoke(
            messages=prompt,
            model_config=model_config
        )
        queries = [
            line.strip(" -\t\r\n")
            for line in result.content.splitlines()
            if line.strip(" -\t\r\n")
        ]
    except Exception:
        queries = []

    merged_queries = [question]

    for query in queries:
        if query not in merged_queries:
            merged_queries.append(query)

    return merged_queries[:5]


def should_use_chat_history(question: str, history=None, model_config=None) -> bool:
    if not history or not model_config:
        return False

    prompt = [
        {
            "role": "system",
            "content": """
            判断最新用户问题是否必须依赖历史对话才能正确回答。
            只回答 yes 或 no。

            如果最新问题是追问、使用代词、省略了主语、询问“为什么”“在哪”“继续”“那这个呢”，
            或者要求对比/纠正上一轮回答，必须知道之前聊了什么才能回答，回答 yes。

            如果最新问题是完整的新主题，不需要历史对话也能回答，回答 no。
            不要回答用户问题，只判断是否依赖历史。
            """
        },
        {
            "role": "user",
            "content": f"""
            最近对话：
            {history or []}

            最新问题：
            {question}
            """
        }
    ]

    try:
        result = invoke(
            messages=prompt,
            model_config=model_config
        )
        answer = result.content.strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False
