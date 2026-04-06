import json
import threading
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
import os
from dotenv import load_dotenv
from agent import app, HumanMessage

load_dotenv()

APP_ID = os.environ.get("LARK_APP_ID", "")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "")

lark_client = lark.Client.builder().app_id(APP_ID).app_secret(APP_SECRET).build()

def process_and_reply(user_text: str, message_id: str) -> None:
    state = {"messages": [HumanMessage(content=user_text)]}
    result = app.invoke(state)
    
    req = ReplyMessageRequest.builder() \
        .message_id(message_id) \
        .request_body(ReplyMessageRequestBody.builder()
                        .content(json.dumps({"text": result["messages"][-1].content}))
                        .msg_type("text").build()) \
        .build()
    lark_client.im.v1.message.reply(req)

def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    msg = data.event.message
    if msg.message_type != "text":
        return
    text = json.loads(msg.content).get("text", "").strip()
    if text:
        threading.Thread(target=process_and_reply, args=(text, msg.message_id)).start()

if __name__ == '__main__':
    handler = lark.EventDispatcherHandler.builder("", "").register_p2_im_message_receive_v1(do_p2_im_message_receive_v1).build()
    ws_client = lark.ws.Client(APP_ID, APP_SECRET, event_handler=handler, log_level=lark.LogLevel.CRITICAL)
    ws_client.start()
