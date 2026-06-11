from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DEFAULT_ORDER_PATH


PRODUCT_SPECS = {
    "XX 蓝牙耳机": {
        "price": "299 元，活动价 249 元",
        "waterproof": "IPX4，可防汗和小雨，不建议游泳佩戴",
        "battery": "单次 8 小时，配合充电盒约 32 小时",
        "strength": "轻便、通话清晰、日常通勤性价比高",
    },
    "YY 游泳耳机": {
        "price": "499 元",
        "waterproof": "IPX8，可用于游泳训练，需按说明清洁并擦干触点",
        "battery": "单次 10 小时，配合充电盒约 40 小时",
        "strength": "高等级防水、运动佩戴稳定",
    },
    "CC 降噪耳机": {
        "price": "699 元",
        "waterproof": "IPX5，可防汗防小雨，不建议浸泡",
        "battery": "开启降噪 6.5 小时，关闭降噪 9 小时",
        "strength": "主动降噪、通勤和办公场景表现更好",
    },
}


class ServiceTools:
    def __init__(self, order_path: Path = DEFAULT_ORDER_PATH):
        self.order_path = order_path
        self.orders = self._load_orders()

    def query_order(self, order_id: str | None) -> dict[str, Any]:
        if not order_id:
            return {"ok": False, "message": "需要订单号才能查询物流。"}
        order = self.orders.get(order_id)
        if not order:
            return {"ok": False, "message": f"没有查到订单 {order_id}，请核对订单号。"}
        return {
            "ok": True,
            "order_id": order_id,
            "status": order["status"],
            "product": order["product"],
            "express": order["express"],
            "tracking_no": order["tracking_no"],
            "eta": order["eta"],
            "message": (
                f"订单 {order_id} 的商品是{order['product']}，当前状态：{order['status']}。"
                f"承运方为{order['express']}，物流单号 {order['tracking_no']}，预计{order['eta']}。"
            ),
        }

    def create_ticket(
        self,
        session_id: str,
        order_id: str | None,
        issue: str,
        action: str,
        priority: str = "normal",
    ) -> dict[str, Any]:
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ticket_id = f"TK{stamp}"
        return {
            "ok": True,
            "ticket_id": ticket_id,
            "session_id": session_id,
            "order_id": order_id or "未提供",
            "issue": issue,
            "action": action,
            "priority": priority,
            "status": "已创建，24 小时内处理",
            "message": (
                f"{action}工单已创建，工单号 {ticket_id}。"
                "我们会在 24 小时内联系您安排后续处理。"
            ),
        }

    def transfer_human(self, reason: str, priority: str = "normal") -> dict[str, Any]:
        return {
            "ok": True,
            "reason": reason,
            "priority": priority,
            "message": f"已为您转接人工客服，优先级：{priority}。人工客服会查看当前对话记录继续处理。",
        }

    def compare_products(self, left: str = "XX 蓝牙耳机", right: str = "YY 游泳耳机") -> dict[str, Any]:
        left_spec = PRODUCT_SPECS.get(left)
        right_spec = PRODUCT_SPECS.get(right)
        if not left_spec or not right_spec:
            return {"ok": False, "message": "暂时只能对比 XX、YY、CC 三款耳机。"}
        rows = []
        labels = {
            "price": "价格",
            "waterproof": "防水",
            "battery": "续航",
            "strength": "适合场景",
        }
        for key, label in labels.items():
            rows.append({"item": label, left: left_spec[key], right: right_spec[key]})
        return {"ok": True, "left": left, "right": right, "rows": rows}

    def _load_orders(self) -> dict[str, dict[str, Any]]:
        if not self.order_path.exists():
            return {}
        data = json.loads(self.order_path.read_text(encoding="utf-8"))
        return {item["order_id"]: item for item in data}
