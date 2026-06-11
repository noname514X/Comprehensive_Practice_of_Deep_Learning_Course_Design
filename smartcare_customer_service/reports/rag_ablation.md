# RAG 检索参数消融实验

## 指标说明

每个问题预先标注 1-2 个正确资料来源；检索返回的 Top-K 文档块中只要包含任一正确来源，就记为命中。

## 结果

| 问题 | Top-1 | Top-3 | Top-5 | Top-3 来源 |
| --- | --- | --- | --- | --- |
| XX 耳机防水吗？可以戴着游泳吗？ | 命中 | 命中 | 命中 | faq.md, faq.md, product_xx_airbuds.md |
| YY 游泳耳机使用后怎么清洁？ | 未命中 | 命中 | 命中 | faq.md, product_yy_swim.md, faq.md |
| CC 降噪耳机适合通勤吗？ | 命中 | 命中 | 命中 | faq.md, product_cc_noise_canceling.md, product_cc_noise_canceling.md |
| 七天无理由退货需要满足什么条件？ | 命中 | 命中 | 命中 | faq.md, after_sales_policy.md, after_sales_policy.md |
| 订单显示签收但我没收到怎么办？ | 命中 | 命中 | 命中 | faq.md, logistics_policy.md, logistics_policy.md |
| 用户很生气时客服怎么处理？ | 命中 | 命中 | 命中 | faq.md, after_sales_policy.md, product_xx_airbuds.md |
| XX 和 YY 两款耳机有什么区别？ | 命中 | 命中 | 命中 | product_yy_swim.md, faq.md, faq.md |
| 发票丢了还能保修吗？ | 命中 | 命中 | 命中 | faq.md, faq.md, after_sales_policy.md |

## 命中率

- Top-1：87.5%
- Top-3：100.0%
- Top-5：100.0%

## 分析

Top-1 对问题表述更敏感，适合回答较明确的问题；Top-3 在召回和上下文长度之间更平衡，因此系统默认使用 top_k=3。Top-5 能提高召回，但会把相邻政策段落一起带入 Prompt，增加回答冗余和潜在干扰。