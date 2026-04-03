# Step0-6 验证：多模型适配兼容性

**验证目标**：确认多模型适配层切换模型时行为正常

---

## 验证项

### 1. 请求格式构造正确

**AnthropicAdapter（Claude API）**：
```json
{
  "model": "claude-sonnet-4-5",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "<base64编码图片>"
          }
        },
        {
          "type": "text",
          "text": "<提示词>"
        }
      ]
    }
  ]
}
```

**OpenAICompatibleAdapter（OpenAI / Qwen / Ollama）**：
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "<提示词>"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,<base64编码图片>"
          }
        }
      ]
    }
  ]
}
```

### 2. 图片编码格式正确

- 支持 PNG、JPEG、GIF 格式
- Base64 编码无误
- media_type 正确识别（image/png、image/jpeg 等）

### 3. 文本提取逻辑正确

- AnthropicAdapter：从 `response.content[].text` 提取
- OpenAICompatibleAdapter：从 `response.choices[0].message.content` 提取
- 处理返回为空的情况

### 4. 错误重试机制

- 默认重试3次
- 每次重试间隔递增（1s、2s、4s）
- 最终失败抛出明确异常

---

## 验收标准

✅ 三个适配器（Anthropic / Qwen / Ollama）均正确构造请求格式
✅ 图片输入格式符合各API规范
✅ 文本提取逻辑正确处理各种响应格式
✅ 错误重试机制正常触发

---

**测试方式**：Mock模式（无需真实API Key）
