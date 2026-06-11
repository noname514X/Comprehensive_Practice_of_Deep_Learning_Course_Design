# SmartCare 测试对话评估结果

## 汇总指标

- 测试样本数：20
- 意图识别准确率：100.0%
- 工具调用正确率：100.0%
- RAG 引用命中率：100.0%
- 覆盖场景：查物流 4 条, 缺少参数 2 条, 退换货 3 条, RAG 问答 5 条, 追问 1 条, 工具对比 1 条, 情绪安抚 1 条, 闲聊 2 条, 转人工 1 条

## 明细

| ID | 用户消息 | 期望意图 | 实际意图 | 期望工具 | 实际工具 | 意图正确 | 工具正确 | 引用数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | 订单号 2024060112345 到哪了？ | order_status | order_status | query_order | query_order | True | True | 0 |
| T02 | 帮我查一下 2024060312347 | order_status | order_status | query_order | query_order | True | True | 0 |
| T03 | 我的快递为什么一直没更新？ | order_status | order_status | - | - | True | True | 0 |
| T04 | 订单 2024060112345 的 XX 耳机左耳没声音，我想换货 | return_exchange | return_exchange | create_ticket | create_ticket | True | True | 0 |
| T05 | 订单 2024060212346 我想退货退款 | return_exchange | return_exchange | create_ticket | create_ticket | True | True | 0 |
| T06 | 我买的耳机坏了 | return_exchange | return_exchange | - | - | True | True | 0 |
| T07 | XX 耳机防水吗？ | product_info | product_info | - | - | True | True | 3 |
| T08 | 能戴着游泳吗？ | product_info | product_info | - | - | True | True | 3 |
| T09 | YY 游泳耳机多少钱？ | product_info | product_info | - | - | True | True | 3 |
| T10 | XX 和 YY 两款耳机有什么区别？ | product_info | product_info | compare_products | compare_products | True | True | 0 |
| T11 | 耳机保修多久？ | warranty | warranty | - | - | True | True | 3 |
| T12 | 你们这什么破服务，再不处理我就投诉了！ | complaint | complaint | transfer_human | transfer_human | True | True | 0 |
| T13 | 快递显示签收但我没收到怎么办？ | order_status | order_status | - | - | True | True | 0 |
| T14 | 今天天气真好 | smalltalk | smalltalk | - | - | True | True | 0 |
| T15 | 订单 2024060412348 物流异常怎么办？ | order_status | order_status | query_order | query_order | True | True | 0 |
| T16 | 我要人工客服 | manual_transfer | manual_transfer | transfer_human | transfer_human | True | True | 0 |
| T17 | 谢谢你 | smalltalk | smalltalk | - | - | True | True | 0 |
| T18 | CC 降噪耳机适合通勤吗？ | product_info | product_info | - | - | True | True | 3 |
| T19 | 发票丢了还能保修吗？ | warranty | warranty | - | - | True | True | 3 |
| T20 | 订单 2024060512349 想维修 | return_exchange | return_exchange | create_ticket | create_ticket | True | True | 0 |

## 结论

规则意图识别在订单、售后、投诉和闲聊场景上表现稳定；RAG 问答能返回来源片段，便于检查答案依据。后续可接入 Sentence-Transformers 与 ChromaDB 替换当前 TF-IDF 检索，以提升语义召回能力。