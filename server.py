import os
import time
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from databricks.sdk import WorkspaceClient

load_dotenv()

mcp = FastMCP("databricks-genie")
client = WorkspaceClient(
    host=os.environ["DATABRICKS_HOST"],
    token=os.environ["DATABRICKS_TOKEN"]
)
SPACE_ID = os.environ["GENIE_SPACE_ID"]

@mcp.tool()
def ask_genie(question: str) -> str:
    """Ask a natural language question to your Databricks Genie Space.
    Genie will translate it to SQL and return the results."""
    # Start conversation
    conv = client.genie.start_conversation(SPACE_ID, question)
    conversation_id = conv.conversation_id
    message_id = conv.message_id

    # Poll for result (max 60 seconds)
    for _ in range(30):
        time.sleep(2)
        msg = client.genie.get_message(SPACE_ID, conversation_id, message_id)
        if msg.status.value in ("COMPLETED", "FAILED", "CANCELLED") or msg.status in ("COMPLETED", "FAILED", "CANCELLED"):
            break

    # Extract status value (it might be an enum or string depending on SDK version)
    status_str = msg.status.value if hasattr(msg.status, "value") else str(msg.status)
    if status_str != "COMPLETED":
        return f"Genie did not complete: {status_str}"

    # Extract text or query result
    output = []
    for block in (msg.attachments or []):
        if block.text:
            output.append(block.text.content)
        if block.query:
            output.append(f"SQL: {block.query.query}\n\nDescription: {block.query.description}")

    if output:
        return "\n\n".join(output)

    return "Genie returned no content."

@mcp.tool()
def list_space_info() -> str:
    """Returns the configured Genie Space ID being used."""
    return f"Connected to Genie Space ID: {SPACE_ID}\nHost: {os.environ['DATABRICKS_HOST']}"

if __name__ == "__main__":
    mcp.run()
