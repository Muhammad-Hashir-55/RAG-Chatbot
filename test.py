from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)

response = llm.invoke([HumanMessage(content="Who are you?")])
print(response.content)
