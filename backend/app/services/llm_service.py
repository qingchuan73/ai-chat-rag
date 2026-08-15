from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI


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

    langchain_messages = to_langchain_messages(messages)
    has_chunk = False

    try:
        for chunk in llm.stream(langchain_messages):
            if chunk.content:
                has_chunk = True
                yield chunk.content
    except ValueError as error:
        if "No generation chunks were returned" not in str(error):
            raise

    if not has_chunk:
        fallback_llm = build_llm(
            model_config=model_config,
            streaming=False,
            temperature=0
        )
        response = fallback_llm.invoke(langchain_messages)
        if response.content:
            yield response.content


def generate_image(prompt: str, model_config):
    image_model = model_config.get("image_model")
    if not image_model:
        raise ValueError("Image model is not configured")

    client = OpenAI(
        api_key=model_config["api_key"],
        base_url=model_config.get("base_url") or None,
    )

    result = client.images.generate(
        model=image_model,
        prompt=prompt,
        size="1024x1024",
        n=1,
    )

    image = result.data[0]
    if getattr(image, "url", None):
        return image.url

    if getattr(image, "b64_json", None):
        return f"data:image/png;base64,{image.b64_json}"

    raise ValueError("Image generation returned no image")
