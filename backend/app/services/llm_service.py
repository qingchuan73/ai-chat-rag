from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


def build_llm(model_config, streaming=False, temperature=0):
    return ChatOpenAI(
        model=model_config["chat_model"],
        api_key=model_config["api_key"],
        base_url=model_config.get("base_url"),
        streaming=streaming,
        temperature=temperature,
    )


def to_langchain_messages(messages):
    all_messages = []

    for message in messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            all_messages.append(
                HumanMessage(content=content)
            )
        elif role == "assistant":
            all_messages.append(
                AIMessage(content=content)
            )
        elif role == "system":
            all_messages.append(
                SystemMessage(content=content)
            )

    return all_messages


def invoke(messages, model_config, temperature=0):
    llm = build_llm(
        model_config=model_config,
        streaming=False,
        temperature=temperature
    )

    return llm.invoke(
        to_langchain_messages(messages)
    )


def chat(messages, model_config):
    llm = build_llm(
        model_config=model_config,
        streaming=True,
        temperature=0
    )

    for chunk in llm.stream(
        to_langchain_messages(messages)
    ):
        if chunk.content:
            yield chunk.content
