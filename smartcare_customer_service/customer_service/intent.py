from __future__ import annotations

import re

from .models import IntentResult


ORDER_RE = re.compile(r"\b(20\d{11,14})\b")

PRODUCT_ALIASES = {
    "xx": "XX 蓝牙耳机",
    "xx耳机": "XX 蓝牙耳机",
    "蓝牙耳机": "XX 蓝牙耳机",
    "yy": "YY 游泳耳机",
    "yy耳机": "YY 游泳耳机",
    "游泳耳机": "YY 游泳耳机",
    "cc": "CC 降噪耳机",
    "降噪耳机": "CC 降噪耳机",
}


class IntentRecognizer:
    def recognize(self, message: str, state: dict[str, str] | None = None) -> IntentResult:
        state = state or {}
        text = message.strip().lower()
        order_id = self.extract_order_id(text)
        product = self.extract_product(text) or state.get("last_product")
        action = self.extract_action(text)
        emotion = self.detect_emotion(text)

        if self._has_any(text, ["投诉", "太差", "破服务", "垃圾", "骗子", "气死", "再不处理"]):
            return IntentResult("complaint", emotion, 0.94, order_id, product, action, "投诉/强烈负面词")

        if order_id and self._has_any(text, ["退", "换", "坏", "没声音", "故障", "质量"]):
            return IntentResult("return_exchange", emotion, 0.93, order_id, product, action, "订单号+售后关键词")

        if self._has_any(text, ["退货", "退款", "换货", "换一个", "维修", "坏了", "没声音", "故障", "质量问题"]):
            return IntentResult("return_exchange", emotion, 0.88, order_id, product, action, "售后关键词")

        if order_id or self._has_any(text, ["订单", "物流", "快递", "发货", "到哪", "到了吗", "查一下"]):
            return IntentResult("order_status", emotion, 0.87, order_id, product, action, "订单/物流关键词")

        if self._has_any(text, ["保修", "质保", "维修", "发票", "售后多久"]):
            return IntentResult("warranty", emotion, 0.8, order_id, product, action, "保修关键词")

        if self._has_any(text, ["防水", "游泳", "续航", "多少钱", "价格", "参数", "区别", "对比", "推荐", "耳机"]):
            return IntentResult("product_info", emotion, 0.82, order_id, product, action, "产品咨询关键词")

        if self._has_any(text, ["人工", "真人", "转接客服", "找客服"]):
            return IntentResult("manual_transfer", emotion, 0.76, order_id, product, action, "用户要求人工客服")

        if self._has_any(text, ["你好", "您好", "谢谢", "天气", "在吗", "嗨"]):
            return IntentResult("smalltalk", emotion, 0.73, order_id, product, action, "闲聊/礼貌用语")

        if state.get("pending_intent") == "return_exchange" and self._has_any(text, ["退", "换", "确认", "可以", "对的"]):
            return IntentResult("return_exchange", emotion, 0.78, order_id, product, action, "延续售后上下文")

        return IntentResult("fallback", emotion, 0.48, order_id, product, action, "未命中高置信规则")

    @staticmethod
    def extract_order_id(text: str) -> str | None:
        match = ORDER_RE.search(text)
        return match.group(1) if match else None

    @staticmethod
    def extract_product(text: str) -> str | None:
        compact = re.sub(r"\s+", "", text.lower())
        for alias, product in PRODUCT_ALIASES.items():
            if alias in compact:
                return product
        return None

    @staticmethod
    def extract_action(text: str) -> str | None:
        if any(keyword in text for keyword in ["换货", "换一个", "换新"]):
            return "换货"
        if any(keyword in text for keyword in ["退货", "退款", "退了"]):
            return "退货退款"
        if "维修" in text:
            return "维修"
        return None

    @staticmethod
    def detect_emotion(text: str) -> str:
        if any(keyword in text for keyword in ["气死", "投诉", "垃圾", "破", "太差", "骗子", "崩溃"]):
            return "angry"
        if any(keyword in text for keyword in ["着急", "急", "马上", "尽快", "催"]):
            return "anxious"
        if any(keyword in text for keyword in ["谢谢", "不错", "满意"]):
            return "positive"
        return "neutral"

    @staticmethod
    def _has_any(text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)
