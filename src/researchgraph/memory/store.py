from langgraph.checkpoint.memory import InMemorySaver


def create_memory():
    """Keep graph checkpoints for the current process."""
    return InMemorySaver()
