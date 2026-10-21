## Lv6 自動測試：Lv6-1 只用鍵盤操作選項、一次按鍵只處理一件事；Lv6-2 衝動機制（張力隨距離與事件變化）。
## 共用操作在 play_base.gd（選選項用方向鍵＋Enter，互動鍵用真正的空白鍵）。執行：zsh tests/run_tests.sh test_lv6
extends "res://tests/play_base.gd"


func run_tests() -> void:
	await run_scene_keys()
	await back_to_title()
	await run_locked_focus()
	await back_to_title()
	await run_title_key()
	await back_to_title()
	await run_impulse()


## 過場的選項：自動聚焦、方向鍵移動、Enter 選擇後只開始打回應，不會同時跳過
func run_scene_keys() -> void:
	print("\n== 過場的選項")
	await start_game()
	main.call("_go_to", { "scene": 6 })
	await to_scene(6)
	await key("interact")                                       # 跳過打字 → 選項出現
	await wait_for(func(): return main.state == CHOOSING, 3.0)
	await press_key(KEY_ENTER)                                  # 選項剛出現就按（想繼續卻按到）
	ok(main.state == CHOOSING, "選項剛出現 0.3 秒內按 Enter：不會誤選")
	await wait_choices()
	ok(focused() == 0, "搜捕隊：選項出現時聚焦第一個")
	await press_key(KEY_DOWN)
	ok(focused() == 1, "方向鍵下：移到第二個")
	await press_key(KEY_UP)
	ok(focused() == 0, "方向鍵上：回到第一個")
	await press_key(KEY_ENTER)
	ok(main.state == TYPING, "Enter 選擇：開始打回應文字（沒有同時跳過打字）")
	await press_key(KEY_SPACE)
	ok(main.state == RESPONSE, "空白鍵一次：只顯示全部文字，還停在回應")
	await press_key(KEY_SPACE)
	await to_scene(7)
	ok(main.current_id == 7, "空白鍵再一次：前往手術台")
	await choose(2); await enter("lab")
	ok(area() == "lab", "手術台用鍵盤選完 → 設施走廊")


## 鎖住的選項不能聚焦；結局的「重新開始」可以用鍵盤
func run_locked_focus() -> void:
	print("\n== 鎖住的選項與結局")
	await start_game()
	main.call("_switch_area", "wall")
	await enter("wall")
	await walk_to(1500); await interact(); await wait_choices()
	ok(locked(0) and locked(1) and focused() == 2, "牆前（記憶 0）：聚焦唯一能選的「永遠遊走」")
	await press_key(KEY_UP)
	ok(focused() == 2, "方向鍵上：不會移到鎖住的選項")
	await choose(2); await to_scene(20)
	await wait_choices()
	ok(focused() == 0, "結局 C：聚焦「重新開始」")
	await press_key(KEY_ENTER)
	await read()
	await wait_for(func(): return main.state == TITLE, 6.0)
	ok(main.state == TITLE, "結局用 Enter 重新開始 → 標題畫面")


## 標題畫面按一次空白鍵：開始遊戲，不會同時關掉停車場的開場
func run_title_key() -> void:
	print("\n== 標題畫面")
	ok(main.state == TITLE, "在標題畫面")
	await press_key(KEY_SPACE)
	await wait_for(func(): return main.state in [TYPING, AREA_TEXT], 5.0)
	ok(area() == "parking_lot" and main.state in [TYPING, AREA_TEXT], "空白鍵一次：開始遊戲，停車場開場正常顯示")


## 衝動機制：離人越近越強，事件選項出現時最強，選完後淡出；人走了之後不再有感覺
func run_impulse() -> void:
	print("\n== 衝動機制（停車場的婦人）")
	await start_game()
	var fx: ColorRect = main.impulse_fx
	var light: Node = player().get_node("Flashlight")   # PointLight2D 或 OmniLight3D
	var base_energy := energy(light)
	ok(target() == 0.0 and not fx.visible, "起點（離婦人很遠）：沒有感覺")
	await walk_to(1150)
	var mid := target()
	ok(mid > 0.0 and mid < 1.0, "走近到 310px：有一點感覺（%.2f）" % mid)
	await seconds(1.0)
	ok(fx.intensity > 0.0 and fx.visible, "紅色暈影慢慢出現")
	await walk_to(1300)
	ok(target() > mid, "再走近：更強（%.2f）" % target())
	await walk_to(1460)
	await wait_choices()
	ok(target() == 1.0, "婦人事件（A5 起先抵抗衝動）：最強")
	await seconds(1.5)
	ok(fx.intensity > 0.9, "強度跟上（%.2f）" % fx.intensity)
	main.call("_finish_resist", true)
	ok(target() == 0.0, "抵抗成功：目標歸零，開始淡出")
	await wait_for(func(): return main.state == CHOOSING and main.choices_ready(), 3.0)
	await select(0)
	await read()
	await seconds(2.0)
	ok(fx.intensity == 0.0 and not fx.visible, "淡出完畢")
	ok(is_equal_approx(energy(light), base_energy), "手電筒回到原本的亮度")
	await walk_to(1460)
	ok(target() == 0.0, "婦人離開後，回到原地也不再有感覺")


func target() -> float:
	return main.call("_impulse_target")


func seconds(t: float) -> void:
	var until := Time.get_ticks_msec() + int(t * 1000)
	while Time.get_ticks_msec() < until:
		await process_frame


func focused() -> int:
	var owner := main.get_viewport().gui_get_focus_owner()
	return owner.get_index() if owner != null and owner.get_parent() == main.choices_box else -1
