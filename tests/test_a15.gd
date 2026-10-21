## A1.5 自動測試：上下左右移動（縱深帶）、影子、頭上的互動提示、互動要走到物件前面、前後排序、spawns 的 [x, y]。
## 共用操作在 play_base.gd。執行：zsh tests/run_tests.sh test_a15
extends "res://tests/play_base.gd"

const TOP := 650.0
const BOTTOM := 735.0


func run_tests() -> void:
	await run_movement()
	await back_to_title()
	await run_prompt_and_depth()
	await back_to_title()
	await run_sorting_and_spawn()
	await back_to_title()
	await run_actions()
	await back_to_title()
	run_spawn_validation()


## 按住方向鍵：上下停在縱深帶邊緣，上下速度約為左右的 0.6 倍
func run_movement() -> void:
	print("\n== 上下左右移動")
	await start_game()
	ok(area() == "parking_lot" and main.state == EXPLORE, "開始遊戲 → 停車場可以走動")
	ok(is_equal_approx(py(), (TOP + BOTTOM) / 2.0), "進入區域時站在縱深帶中間")
	await hold("move_up", 120)
	ok(is_equal_approx(py(), TOP), "按住上：停在縱深帶上緣 %d" % TOP)
	await hold("move_down", 200)
	ok(is_equal_approx(py(), BOTTOM), "按住下：停在縱深帶下緣 %d" % BOTTOM)
	# 速度比用自己的單位量：2D 是畫面像素，3D 是公尺（3D 的縱深帶 85 像素對應 3 公尺，換成像素比例會不同）
	var y0: float = player().position.z if is_3d() else player().position.y
	await hold("move_up", 30)
	var dy: float = y0 - (player().position.z if is_3d() else player().position.y)
	var x0: float = player().position.x
	await hold("move_right", 30)
	var dx: float = player().position.x - x0
	ok(dy > 0.0 and absf(dy / dx - 0.6) < 0.05, "上下速度約為左右的 0.6 倍（%.2f / %.2f）" % [dy, dx])
	if is_3d():
		var sprite: GeometryInstance3D = player().get_node("Sprite")
		ok(sprite.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "3D：主角會投出影子（燈的真陰影，不用 2D 的影子圖）")
	else:
		var shadow := player().get_node_or_null("Shadow")
		ok(shadow != null and shadow.get_index() < player().get_node("Sprite").get_index(), "主角腳下有影子，畫在角色下面")


## 互動提示：要靠近物件、站在物件前面的地面才出現；提示浮在主角頭上
func run_prompt_and_depth() -> void:
	print("\n== 提示與互動深度")
	await start_game()
	await walk_xy(1100, 680)
	ok(prompt() == "", "離地面殘骸 100：還沒有提示")
	await walk_xy(1060, 680)
	ok(prompt().contains("地面殘骸"), "離地面殘骸 60：出現提示")
	await frames(2)
	var head_y: float = main.get("_area").player_head_screen().y
	var label: Label = main.prompt_label
	ok(label.position.y + label.size.y <= head_y and label.position.y > head_y - 80.0, "提示浮在主角頭上")
	await walk_xy(1000, 712)
	ok(prompt() == "", "站在縱深帶外側（y 712）：不會觸發地面殘骸")
	await walk_xy(1000, 660)
	await interact()
	ok(main.state in [TYPING, AREA_TEXT], "站到殘骸前面按互動鍵：可以調查")
	await read()
	# 人物事件（靠近觸發）涵蓋整個縱深帶：從最外側走過去也會遇到
	await walk_xy(1480, BOTTOM)
	await wait_for(func(): return main.state in [TYPING, AREA_TEXT], 3.0)
	ok(main.state in [TYPING, AREA_TEXT], "從縱深帶最外側走向婦人：照樣觸發事件")


## 前後排序（y_sort）與 spawns 的 y
func run_sorting_and_spawn() -> void:
	print("\n== 前後排序與出生點")
	await start_game()
	var a: Node = main.get("_area")
	if is_3d():
		# 3D 的前後由深度決定：婦人在縱深帶中間、近景在走道前面（鏡頭那一側）
		var near_z: float = a.get_node("Near/Papers1").position.z
		ok(near_z > a.get("depth") / 2.0, "3D：近景物件在走道前面（z %.2f）" % near_z)
	else:
		ok(a.y_sort_enabled and a.get_node("Points").y_sort_enabled and a.get_node("Near").y_sort_enabled, "區域、互動點、近景都依 y 排序")
		ok((a.get_node("FrontLayer") as CanvasItem).z_index > 0, "前景層永遠畫在最前面")
	var woman_y := point_y("Woman")
	ok(woman_y > TOP and woman_y < BOTTOM, "婦人站在路中間（y %d）" % woman_y)
	a.call("place_player", 500.0, 720.0)
	ok(is_equal_approx(py(), 720.0), "place_player(x, y)：放到指定的 y")
	a.call("place_player", 500.0, 900.0)
	ok(is_equal_approx(py(), BOTTOM), "place_player 的 y 超出縱深帶：限制在邊緣")
	a.call("place_player", 600.0)
	ok(is_equal_approx(py(), BOTTOM) and is_equal_approx(px(), 600.0), "place_player 只給 x：y 不變")


## A3：調查時轉向物件並伸手、文字關掉後恢復；衝動強度高時站著前傾
func run_actions() -> void:
	print("\n== 主角的新動作（A3）")
	await start_game()
	var sprite: Node = player().get_node("Sprite")
	await walk_xy(1060, 660)
	player().face(1)                                   # 先背對地面殘骸（殘骸在左邊 x 1000）
	await interact()
	ok(sprite.animation == "reach_left" and player().get("acting"), "調查地面殘骸：主角轉向殘骸並伸手（%s）" % sprite.animation)
	await read()
	await physics(2)
	ok(not player().get("acting") and sprite.animation.begins_with("idle_"), "文字關掉後手放下、回到待機")
	await walk_xy(1300, 700)                           # 婦人在 1500：衝動漸強，還不會觸發事件
	await wait_for(func(): return main.impulse_fx.intensity >= 0.5, 3.0)
	await physics(2)
	ok(sprite.animation == "lean_right", "衝動強度高、站著不動：主角朝婦人（右邊）前傾（%s）" % sprite.animation)
	await walk_xy(400, 700)
	await wait_for(func(): return main.impulse_fx.intensity < 0.5, 3.0)
	await physics(2)
	ok(sprite.animation.begins_with("idle_"), "離開後衝動降低：恢復待機")


## 劇本檢查認得 spawns 的 [x, y]，故意寫錯會報錯
func run_spawn_validation() -> void:
	print("\n== spawns 格式檢查")
	var areas: AreaData = main.get("areas")
	var story: StoryData = main.get("story")
	var spawns: Dictionary = areas.get_area("parking_lot")["spawns"]
	var backup := spawns.duplicate()
	spawns["street"] = [2150, 700]
	ok(not has_spawn_error(areas.validate(story)), "spawns 寫 [x, y]：通過檢查")
	spawns["street"] = [2150]
	ok(has_spawn_error(areas.validate(story)), "spawns 只有一個數字的陣列：報錯")
	spawns["street"] = "2150"
	ok(has_spawn_error(areas.validate(story)), "spawns 寫成字串：報錯")
	spawns.clear()
	spawns.merge(backup)


# ---- 這個測試專用的操作 ----

func hold(action: String, physics_frames: int) -> void:
	Input.action_press(action)
	await physics(physics_frames)
	Input.action_release(action)
	await physics(2)


func walk_xy(x: float, y: float) -> void:
	set_player(x, y)
	await physics(4)
	await wait_for(func(): return main.state != TRANSITION, 3.0)


func has_spawn_error(errors: Array[String]) -> bool:
	for e in errors:
		if e.contains("spawns.street 格式不對"):
			return true
	return false
