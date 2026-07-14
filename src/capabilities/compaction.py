import copy

SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful AI."}
BOILERPLATE_PREFIXES = [
    "Sure! ",
    "Sure, ",
    "Of course! ",
    "Of course, ",
    "Great question! ",
    "That's a great question! ",
    "Absolutely! ",
    "Certainly! ",
    "I'd be happy to help! ",
    "I'd be happy to help you with that! ",
    "Let me help you with that. ",
]


def strip_boilerplate(messages):
    for msg in messages:
        if msg.get("role") == "assistant":
            for prefix in BOILERPLATE_PREFIXES:
                if msg["content"].startswith(prefix):
                    new_content = msg["content"][len(prefix) :]
                    if new_content.strip():
                        msg["content"] = new_content
                    break  # strip only the first matching
    return messages


def apply_sliding_window(messages, limit=10):
    if len(messages) <= limit:
        return messages
    sys_msg = [messages[0]] if messages[0].get("role") == "system" else []

    # We want to keep the system message + most recent (limit - len(sys_msg)) messages
    keep_count = limit - len(sys_msg)
    if keep_count <= 0:
        return sys_msg
    return sys_msg + messages[-keep_count:]


def compact_context(messages):
    msgs_copy = copy.deepcopy(messages)

    # Ensure system prompt is at index 0
    if not msgs_copy or msgs_copy[0].get("role") != "system":
        msgs_copy.insert(0, SYSTEM_PROMPT.copy())
    else:
        msgs_copy[0] = SYSTEM_PROMPT.copy()

    msgs_copy = strip_boilerplate(msgs_copy)
    msgs_copy = apply_sliding_window(msgs_copy)
    return msgs_copy
