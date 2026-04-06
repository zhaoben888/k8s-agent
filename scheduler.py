import time
import requests
import schedule
import hmac
import hashlib
import base64
from agent import app, HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
FEISHU_SECRET = os.environ.get("FEISHU_SECRET", "")

def send_feishu_alert(content):
    timestamp = str(int(time.time()))
    string_to_sign = f"{timestamp}\n{FEISHU_SECRET}"
    sign = base64.b64encode(hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()).decode('utf-8')
    
    requests.post(FEISHU_WEBHOOK, headers={"Content-Type": "application/json"}, json={
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "text", 
        "content": {"text": f"[K8S 告警]\n{content}"}
    })

def k8s_inspection_job():
    ins = (
        "集群巡检：检查节点、default命名空间的Pod和Deployment。\n"
        "正常只回复'正常'，异常才说明资源名称和状态。"
    )
    state = {"messages": [HumanMessage(content=ins)], "current_namespace": "default"}
    try:
        for event in app.stream(state, stream_mode="values"): 
            pass
        ans = event["messages"][-1].content
        # 只有在发现异常时才发送告警
        if "正常" not in ans or "异常" in ans.lower() or "error" in ans.lower() or "crashloop" in ans.lower():
            send_feishu_alert(ans)
    except Exception as e:
        send_feishu_alert(f"巡检失败: {str(e)}")

if __name__ == "__main__":
    schedule.every(2).minutes.do(k8s_inspection_job)
    k8s_inspection_job()
    while True:
        schedule.run_pending()
        time.sleep(1)
