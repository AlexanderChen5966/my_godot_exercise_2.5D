## 遊玩測試的共用操作（test_lv4.gd、test_lv5.gd 繼承這個檔案）：載入真正的 Main.tscn，用和玩家一樣的輸入（互動鍵、按選項）操作。
## 檔名不是 test_ 開頭，run_tests.sh 不會單獨執行它。
extends SceneTree

const TITLE := 0
const TRANSITION := 1
const TYPING := 2
const CHOOSING := 3
const RESPONSE := 4
const EXPLORE := 5
const AREA_TEXT := 6
const RESIST := 9  # A5 壓抑衝動（連打）

var main: Control
var fails := 0
var checks := 0


## 載入主場景、執行 run_tests()、印出結果並結束（子類別覆寫 run_tests）
func _initialize() -> void:
	# A6：測試用自己的設定檔，從預設值開始（測試副本和編輯器共用同一個使用者資料夾，不能讀到、改到作者實際的設定）
	GameSettings.path = "user://settings_test.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(GameSettings.path))
	main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	# B1：預設在 2D 區域上測；AREAS_3D=1 時改用 3D 區域（還沒做 3D 版的區域照舊是 2D）
	main.use_3d_areas = OS.get_environment("AREAS_3D") == "1"
	root.add_child(main)
	await frames(5)
	await run_tests()
	print("\n共 %d 項檢查，失敗 %d 項" % [checks, fails])
	main.queue_free()
	await frames(3)
	quit(1 if fails > 0 else 0)


func run_tests() -> void:
	pass


# ---- 操作 ----

func start_game(skip_intro := true) -> void:
	main.call("_start_game")
	await wait_for(func(): return main.state in [TYPING, AREA_TEXT], 5.0)
	if skip_intro:
		await read()


func back_to_title() -> void:
	main.call("_return_to_title")
	await wait_for(func(): return main.state == TITLE, 5.0)


## 主角走到 x（直接設定位置，再等物理更新讓互動點偵測到）
func walk_to(x: float) -> void:
	player().position.x = x
	await physics(4)
	await wait_for(func(): return main.state != TRANSITION, 3.0)


func interact() -> void:
	await key("interact")


## 讀完目前的文字：打字中先按一次顯示全部，再按一次關閉
func read() -> void:
	await wait_for(func(): return main.state in [TYPING, AREA_TEXT, RESPONSE], 5.0)
	# A5 壓抑衝動判定後會鎖住按鍵一下（玩家連打時才不會跳過文字），等鎖解除再按
	await wait_for(func(): return Time.get_ticks_msec() >= int(main.get("_input_locked_until")), 2.0)
	if main.state == TYPING:
		await key("interact")
	await wait_for(func(): return main.state in [AREA_TEXT, RESPONSE], 3.0)
	await key("interact")
	await wait_for(func(): return main.state in [EXPLORE, TRANSITION, CHOOSING] or main.current_id >= 3, 3.0)


## 等選項出現（打字中先按一次），用方向鍵移到第 index 個選項、按 Enter，再讀完回應
func choose(index: int) -> void:
	await wait_choices()
	if main.state == RESIST:
		# A5 壓抑衝動：要選的是「撲上去」（fail）就判定抵抗失敗（自動撲上去）；其他選項先判定成功，
		# 成功後 fail 那個選項會隱藏，後面的編號往前一格。真正的連打與時限在 test_a5 測。
		var fail: int = main.resist_fail_index()
		if index == fail:
			main.call("_finish_resist", false)
			await read()
			return
		main.call("_finish_resist", true)
		await wait_for(func(): return main.state == CHOOSING and main.choices_ready(), 3.0)
		if index > fail:
			index -= 1
	await select(index)
	await read()


## 用真正的按鍵選選項：方向鍵移動焦點，Enter 按下（和玩家一樣）
func select(index: int) -> void:
	var target := main.choices_box.get_child(index) as Button
	for i in main.choices_box.get_child_count():
		if target.has_focus():
			break
		var current := main.get_viewport().gui_get_focus_owner()
		var down := current == null or current.get_index() < index
		await press_key(KEY_DOWN if down else KEY_UP)
	if not target.has_focus():
		print("    ⚠ 方向鍵移不到第 %d 個選項" % index)
	await press_key(KEY_ENTER)


func wait_choices() -> void:
	await wait_for(func(): return main.state in [TYPING, CHOOSING, RESIST], 5.0)
	if main.state == TYPING:
		await key("interact")
	await wait_for(func(): return main.state == RESIST or (main.state == CHOOSING and main.choices_ready()), 3.0)


## 第 index 個選項是否鎖住（數值不夠：灰色、不能按）
func locked(index: int) -> bool:
	return (main.choices_box.get_child(index) as Button).disabled


## 走到出口、按互動鍵、讀完出口文字，等新區域的開場（第一次）並讀完
func go_exit(x: float, next_area: String) -> void:
	await walk_to(x)
	await interact()
	if main.state in [TYPING, AREA_TEXT]:
		await read()
	await enter(next_area)


## 走到通往過場的出口，讀完出口文字，等過場出現
func exit_to_scene(x: float, scene_id: int) -> void:
	await walk_to(x)
	await interact()
	await read()
	await to_scene(scene_id)


## 等進入區域（換場結束），有開場就讀完
func enter(area_id: String) -> void:
	await wait_for(func(): return area() == area_id and main.state != TRANSITION, 6.0)
	if main.state in [TYPING, AREA_TEXT]:
		await read()


## 等過場或結局出現
func to_scene(scene_id: int) -> void:
	await wait_for(func(): return main.current_id == scene_id and main.state in [TYPING, CHOOSING], 6.0)


## 結局／Bad End 的選項（回應是空的，按下去直接重試或回標題）
func end_choice(index: int) -> void:
	await wait_choices()
	await select(index)
	await wait_for(func(): return main.state != CHOOSING, 3.0)


## 互動鍵用真正的空白鍵（同時符合 interact 與 ui_accept，可以測到按鍵衝突）
func key(action: String) -> void:
	if action == "interact":
		await press_key(KEY_SPACE)
		return
	var press := InputEventAction.new()
	press.action = action
	press.pressed = true
	Input.parse_input_event(press)
	await frames(2)
	var release := InputEventAction.new()
	release.action = action
	release.pressed = false
	Input.parse_input_event(release)
	await frames(2)


# ---- 查詢 ----

func gs() -> GameStateData:
	return root.get_node("GameState")


func area() -> String:
	return main.get("_area_id")


func player() -> CharacterBody2D:
	return main.get("_area").get_node("Player")


func prompt() -> String:
	return main.prompt_label.text if main.prompt_label.visible else ""


func figure_visible(point_name: String) -> bool:
	return main.get("_area").get_node("Points/%s/Figure" % point_name).visible


func ok(cond: bool, name: String) -> void:
	checks += 1
	print(("  ✓ " if cond else "  ✗ ") + name)
	if not cond:
		fails += 1
		print("    狀態 state=%d area=%s scene=%d stats=%s items=%s flags=%s" % [main.state, area(), main.current_id, gs().stats, gs().items.keys(), gs().flags.keys()])


# ---- 等待 ----

func frames(n: int) -> void:
	for i in n:
		await process_frame


func physics(n: int) -> void:
	for i in n:
		await physics_frame


## 以真實時間計算逾時（headless 不等螢幕更新，畫格會跑得很快，但淡入淡出與打字是用秒計算）
func wait_for(cond: Callable, timeout: float) -> void:
	var until := Time.get_ticks_msec() + int(timeout * 1000)
	while not cond.call() and Time.get_ticks_msec() < until:
		await process_frame


## 送出一次真正的按鍵（按下＋放開）；keycode 與 physical_keycode 都設定，符合專案用實體按鍵綁定的動作
func press_key(code: Key) -> void:
	for pressed in [true, false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = pressed
		Input.parse_input_event(event)
		await frames(2)
