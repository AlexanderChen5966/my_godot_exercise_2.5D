#!/bin/zsh
# 在「拿掉 MCP 外掛的專案副本」上執行劇本檢查與遊玩測試。
# 不直接對專案跑 headless：外掛的 MCPRuntimeServer 在 headless 也會啟動，會蓋掉 godot-mcp-toolkit 的 runtime 登錄。
# 用法（在專案根目錄）：zsh tests/run_tests.sh            劇本檢查＋所有 tests/test_*.gd（2D 區域、3D 區域各跑一次）
#                      zsh tests/run_tests.sh test_lv4   只跑指定的測試
#                      AREAS_3D=0 或 1 zsh tests/run_tests.sh   只跑 2D 或只跑 3D（B1）
set -u
PROJECT="${0:A:h:h}"
GODOT="${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}"
COPY="${TMPDIR:-/tmp}/shiyuzhe_test_copy"

echo "== 建立副本：$COPY"
mkdir -p "$COPY"
rsync -a --delete --exclude addons/ --exclude .mcp.json --exclude build/ --exclude .git/ "$PROJECT/" "$COPY/"
sed -i '' '/^MCPRuntimeServer=/d; /^enabled=PackedStringArray("res:\/\/addons\/godot_mcp_toolkit\/plugin.cfg")/d' "$COPY/project.godot"
"$GODOT" --headless --path "$COPY" --import >/dev/null 2>&1

fails=0
echo "\n== 劇本檢查"
"$GODOT" --headless --path "$COPY" --script res://tools/validate_story.gd 2>&1 | grep -v "^Godot Engine\|^$"
[ ${pipestatus[1]} -eq 0 ] || fails=$((fails + 1))

# B1：同一套測試在 2D 區域與 3D 區域上各跑一次（play_base.gd 依 AREAS_3D 切換）
if [ -n "${AREAS_3D:-}" ]; then modes=("$AREAS_3D"); else modes=(0 1); fi
for mode in $modes; do
for test in "$COPY"/tests/test_*.gd; do
	name="${test:t:r}"
	[ $# -gt 0 ] && [ "$name" != "$1" ] && continue
	label="2D"; [ "$mode" = "1" ] && label="3D"
	echo "\n== $name（$label）"
	out=$(AREAS_3D=$mode "$GODOT" --headless --path "$COPY" --script "res://tests/$name.gd" 2>&1)
	code=$?
	print -r -- "$out" | grep -v "^Godot Engine\|^$\|leaked at exit\|still in use at exit\|at: cleanup\|at: clear"
	# 腳本載入失敗（例如 Parse Error）時 Godot 的結束碼仍是 0，所以也看輸出：有 SCRIPT ERROR 或沒有印出結果都算失敗
	if [ $code -ne 0 ] || print -r -- "$out" | grep -q "SCRIPT ERROR" || ! print -r -- "$out" | grep -q "項檢查"; then
		fails=$((fails + 1))
		print -r -- "$out" | grep -q "項檢查" || echo "✗ $name（$label）沒有執行完（腳本錯誤或卡住）"
	fi
done
done

echo ""
if [ $fails -eq 0 ]; then echo "✓ 全部通過"; else echo "✗ 有 $fails 項失敗"; fi
exit $fails
