from .app.services.llm_agent import handle_chat
from .app.schemas.chat import ChatRequest

payload = ChatRequest(
    business_id="demo",
    session_id="test1",
    message="¿Tienes disponibilidad mañana?"
)

response = handle_chat(payload)
print(response)
