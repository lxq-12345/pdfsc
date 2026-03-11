#!/bin/bash
# 配置驱动的快照处理器
# 从会话管理协议.md读取规则，自动识别快照触发

PROTOCOL_FILE="会话管理协议.md"
SNAPSHOT_DIR="mem/snapshot"
BUFFER_FILE="mem/.snapshot_buffer.md"

echo "=== 快照配置驱动处理器 ==="
echo ""

# 从协议文件读取关键词
echo "【1】从协议读取关键词配置"

# 提取快照触发关键词（使用sed）
# 格式: 快照触发：    "快照" / "保存快照"
# 提取第一个引号内的内容和第二个引号内的内容
SNAPSHOT_KEYWORDS=$(grep "快照触发：" "$PROTOCOL_FILE" | sed -n 's/.*"\([^"]*\)".*/\1/;p' | tr '\n' '|' | sed 's/|$//')

# 提取结束归档关键词
ARCHIVE_KEYWORDS=$(grep "结束归档：" "$PROTOCOL_FILE" | sed -n 's/.*"\([^"]*\)".*/\1/;p' | tr '\n' '|' | sed 's/|$//')

echo "✅ 已加载规则:"
echo "   快照触发: $SNAPSHOT_KEYWORDS"
echo "   结束归档: $ARCHIVE_KEYWORDS"
echo ""

# 测试关键词识别
test_trigger() {
    USER_MESSAGE="$1"
    echo "【2】检查消息: '$USER_MESSAGE'"

    # 检查快照触发
    if echo "$USER_MESSAGE" | grep -qE "$SNAPSHOT_KEYWORDS"; then
        echo "   ✅ 匹配: 快照触发"
        return 0  # 触发快照
    fi

    # 检查归档触发
    if echo "$USER_MESSAGE" | grep -qE "$ARCHIVE_KEYWORDS"; then
        echo "   ✅ 匹配: 结束归档"
        return 1  # 触发归档
    fi

    echo "   ⊗ 无匹配"
    return 2  # 无触发
}

# 生成快照
generate_snapshot() {
    CONVERSATION="$1"
    TIMESTAMP=$(date +%Y-%m-%d-%H%M)
    SNAPSHOT_FILE="$SNAPSHOT_DIR/快照-$TIMESTAMP.md"

    echo "   生成快照文件: $SNAPSHOT_FILE"
    echo "$CONVERSATION" > "$SNAPSHOT_FILE"
    echo "   ✅ 快照已保存"
}

# 性能测试
echo "【3】执行快照流程测试"
echo ""

CONV_TEXT="时间段：11:00 - 11:05

用户：快照

Claude：正在处理快照
"

test_trigger "快照"
if [ $? -eq 0 ]; then
    echo "【4】执行快照生成"
    generate_snapshot "$CONV_TEXT"
fi

echo ""
echo "✅ 配置驱动快照处理验证完毕"
