## A5 自動測試：手勢（G 鍵比出「我——在——這——裡」）、人物的反應文字、沒有對象時的獨白、只反應一次、事件發生後不再反應、
## 比手勢時不能移動也不接受其他按鍵、對話中按 G 沒有作用、按鍵提示、數值不變（方案 A）、劇本檢查。
## 記憶閃回：調查關鍵物品時先閃回原插畫再顯示文字、可以跳過、一輪一次、診療椅沒有錄音筆時不閃回、劇本檢查。
## 躲藏：警衛轉身、被光照到 → 被發現的警衛事件、掩護裡不會被發現、移動就出來、通風管 → 從另一頭出來、警衛事件結束。
## 壓抑衝動：按住（測試版）或連打（正式版）成功 → 撲上去隱藏、失敗（時限）→ 自動撲上去、判定後鎖住按鍵、妻子失敗 → Bad End、重試重新抵抗、女兒不抵抗、劇本檢查。
## 共用操作在 play_base.gd。執行：zsh tests/run_tests.sh test_a5
extends "res://tests/play_base.gd"

const GESTURE := 7  # main.gd 的 State.GESTURE
const FLASHBACK := 8


func run_tests() -> void:
	await run_gesture_alone()
	await run_gesture_woman()
	await back_to_title()
	await run_flashback()
	await back_to_title()
	await run_resist()
	await back_to_title()
	await run_hide()
	await back_to_title()
	run_validation()


func gesture() -> void:
	await press_key(KEY_G)


## 等手勢播完（約 2 秒）
func wait_gesture_done() -> void:
	await wait_for(func(): return main.state != GESTURE, 4.0)


func run_gesture_alone() -> void:
	print("\n== 沒有對象")
	await start_game()
	ok(main.get("_gesture_hint").visible, "第一次可以走動：畫面下方顯示「G　比出手勢」")
	var stats: Dictionary = gs().stats.duplicate()
	var x := px()
	await gesture()
	ok(main.state == GESTURE and String(player().get_node("Sprite").animation).begins_with("gesture_"), "按 G：主角比出手勢")
	ok(main.sound_log.back() == "inspect_4.ogg", "比手勢時有布料聲")
	Input.action_press("move_right")
	await physics(30)
	Input.action_release("move_right")
	ok(is_equal_approx(px(), x), "比手勢時不能移動")
	await press_key(KEY_SPACE)
	ok(main.state == GESTURE, "比手勢時按互動鍵沒有作用")
	await wait_gesture_done()
	ok(main.state in [TYPING, AREA_TEXT] and main.body.text.contains("含糊"), "附近沒有人、第一次：比完顯示獨白")
	await read()
	ok(main.state == EXPLORE, "讀完獨白：可以繼續走動")
	await gesture()
	await wait_gesture_done()
	ok(main.state == EXPLORE, "第二次（沒有對象）：只有動畫，沒有文字")
	ok(gs().stats == stats, "比手勢不改變數值（方案 A）")


func run_gesture_woman() -> void:
	print("\n== 對婦人比手勢")
	await walk_to(1250)
	ok(main.state == EXPLORE and main.gesture_target() == "woman", "離婦人 250 px：事件還沒觸發，手勢的對象是婦人")
	player().face(-1)
	await gesture()
	ok(player().facing == 1, "比手勢時先轉向婦人")
	await wait_gesture_done()
	ok(main.state in [TYPING, AREA_TEXT] and main.body.text.contains("婦人僵在原地") and main.scene_title.text == "婦人", "比完：顯示婦人的反應")
	ok(gs().has_flag("parking_lot.woman.gesture"), "設定旗標 parking_lot.woman.gesture（之後的事件可以用）")
	await read()
	await gesture()
	await wait_gesture_done()
	ok(main.state == EXPLORE, "再對婦人比一次：不再反應（每人一輪一次）")

	# 對話中按 G 沒有作用
	await walk_to(1000); await interact()
	await gesture()
	ok(main.state in [TYPING, AREA_TEXT] and not String(player().get_node("Sprite").animation).begins_with("gesture_"), "調查文字打開時按 G：沒有作用")
	await read()

	# 婦人的事件發生後（逃走），不再是手勢的對象
	await walk_to(1460)
	await choose(0)
	await wait_for(func(): return main.state == EXPLORE, 3.0)
	gs().flags.erase("parking_lot.woman.gesture")
	await walk_to(1250)
	ok(main.gesture_target() == "", "婦人逃走後：不再是手勢的對象")


func run_flashback() -> void:
	print("\n== 記憶閃回")
	await start_game()
	await walk_to(300)
	var started := Time.get_ticks_msec()
	await interact()
	ok(main.state == FLASHBACK, "調查「醒來的地方」：進入記憶閃回")
	ok(main.sound_log.back() == "flashback", "閃回音")
	await wait_for(func(): return main.flashback.visible, 1.0)
	ok(main.flashback.visible and main.flashback.texture.resource_path.ends_with("scene_19.webp"), "白光之後出現插畫 scene_19（加上閃回 shader）")
	await wait_for(func(): return main.state in [TYPING, AREA_TEXT], 5.0)
	var took := (Time.get_ticks_msec() - started) / 1000.0
	ok(main.state in [TYPING, AREA_TEXT] and main.body.text.contains("照片") and not main.flashback.visible, "閃回結束（%.1f 秒）：回到區域，顯示原本的調查文字" % took)
	ok(took >= 2.5 and took <= 4.0, "閃回約 3 秒")
	await read()
	# 再調查一次（清掉「已調查」，保留「已閃回」）：不再閃回
	gs().flags.erase("parking_lot.wake")
	await interact()
	ok(main.state in [TYPING, AREA_TEXT], "同一輪再調查：不再閃回，直接顯示文字")
	await read()
	# 跳過：清掉兩個旗標再調查，閃回中按互動鍵
	gs().flags.erase("parking_lot.wake")
	gs().flags.erase("parking_lot.wake.flashback")
	await interact()
	await frames(10)
	started = Time.get_ticks_msec()
	await press_key(KEY_SPACE)
	await wait_for(func(): return main.state in [TYPING, AREA_TEXT], 3.0)
	ok(main.state in [TYPING, AREA_TEXT] and (Time.get_ticks_msec() - started) < 1200, "閃回中按互動鍵：跳過，馬上回到區域")
	await read()
	# 診療椅：只有拿到錄音筆的 variant 才閃回
	var chair: Dictionary = main.areas.get_area("clinic")["points"]["chair"]
	ok(not AreaData.view(chair, gs()).has("flashback"), "診療椅（沒有錄音筆）：不閃回")
	gs().add_item("recorder")
	ok(AreaData.view(chair, gs()).get("flashback", "") == "scene_05.webp", "診療椅（有錄音筆）：閃回 scene_05")


func wait_resist() -> void:
	await wait_for(func(): return main.state in [TYPING, RESIST], 5.0)
	if main.state == TYPING:
		await key("interact")
	await wait_for(func(): return main.state == RESIST, 3.0)


func run_resist() -> void:
	print("\n== 壓抑衝動")
	await start_game()
	var humanity: int = gs().stats["humanity"]
	await walk_to(1460)
	await wait_resist()
	ok(main.choices_box.get_child_count() == 0, "抵抗中沒有選項")
	if main.RESIST_HOLD:
		# 測試版：按住空白鍵（main.gd 的 RESIST_HOLD = true）
		ok(main.state == RESIST and main.resist_box.visible and main.resist_label.text == "按住【空白鍵】抵抗", "婦人：事件文字後出現「按住【空白鍵】抵抗」與量表，選項還沒出現")
		space(true)
		await seconds(0.5)
		space(false)
		var v: float = main.resist_value
		await seconds(0.6)
		ok(v > 0.2 and main.resist_value < v, "按住會漲（%.2f），放開會往下掉（%.2f）" % [v, main.resist_value])
		space(true)
		await wait_for(func(): return main.state != RESIST, 3.0)
		ok(main.state != RESIST and main.hint.visible and main.hint.text == "你咬緊牙，那股衝動慢慢退去。", "按住到滿（婦人 1.5 秒）：成功，顯示「你咬緊牙，那股衝動慢慢退去。」")
		await seconds(1.5)
		ok(main.state != CHOOSING, "還按著空白鍵：選項不會出現（放開才出現，避免一出現就被選到）")
		space(false)
	else:
		# 正式版：連打
		ok(main.state == RESIST and main.resist_box.visible and main.resist_label.text == "連打【空白鍵】抵抗", "婦人：事件文字後出現「連打【空白鍵】抵抗」與量表，選項還沒出現")
		for i in 3:
			await press_key(KEY_SPACE)
		var v: float = main.resist_value
		await seconds(0.6)
		ok(v > 0.2 and main.resist_value < v, "連打會漲（%.2f），停下來會往下掉（%.2f）" % [v, main.resist_value])
		for i in 30:
			if main.state != RESIST:
				break
			await press_key(KEY_SPACE)
		ok(main.state != RESIST and main.hint.visible and main.hint.text == "你咬緊牙，那股衝動慢慢退去。", "連打到滿：成功，顯示「你咬緊牙，那股衝動慢慢退去。」")
		await press_key(KEY_ENTER)
		ok(main.state != CHOOSING or main.choices_box.get_child_count() == 1, "判定後鎖住按鍵：繼續連打不會選到選項")
	await wait_for(func(): return main.state == CHOOSING and main.choices_ready(), 3.0)
	ok(main.choices_box.get_child_count() == 1 and (main.choices_box.get_child(0) as Button).text == "強行壓制自己", "成功：「撲上去」不見了，只剩「強行壓制自己」")
	await select(0)
	await read()
	ok(gs().stats["humanity"] == humanity + 1, "選強行壓制自己：人性 +1")
	await back_to_title()

	# 失敗：什麼都不按，時限到了自動撲上去
	await start_game()
	await walk_to(1460)
	await wait_resist()
	await wait_for(func(): return main.state != RESIST, 7.0)
	ok(main.sound_log.back() == "growl" and main.choices_box.get_child_count() == 0, "時限到了沒漲滿：自動撲上去（低吼）")
	await read()
	ok(gs().stats["humanity"] == humanity - 1, "自動撲上去：人性 −1（等於選了撲上去）")

	# 妻子：失敗 → Bad End「噬語」；重試後重新抵抗
	main.call("_switch_area", "ruins")
	await enter("ruins")
	await walk_to(1600)
	await wait_resist()
	ok(main.state == RESIST and main.resist_fail_index() == 2, "避難所的妻子：也要抵抗，失敗等於「撲向她」")
	main.call("_finish_resist", false)
	await read()
	await to_scene(23)
	ok(main.current_id == 23, "抵抗失敗：Bad End「噬語」")
	await end_choice(0)
	await enter("ruins")
	await walk_to(1600)
	await wait_resist()
	ok(main.state == RESIST, "從這裡重試：回到廢墟，靠近妻子時重新抵抗")
	ok(not main.areas.get_area("home")["points"]["daughter"].has("resist"), "女兒不抵抗（她會直接跑掉）")


## 按下／放開真正的空白鍵（按住版用：不送放開，就是一直按著）
func space(pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_SPACE
	event.physical_keycode = KEY_SPACE
	event.pressed = pressed
	Input.parse_input_event(event)


func seconds(t: float) -> void:
	var until := Time.get_ticks_msec() + int(t * 1000)
	while Time.get_ticks_msec() < until:
		await process_frame


func to_lab() -> void:
	await start_game()
	main.call("_switch_area", "lab")
	await enter("lab")


## 主角瞬移到 (x, y)，等物理更新讓互動點偵測到
func place(x: float, y: float) -> void:
	set_player(x, y)
	await physics(4)


func run_hide() -> void:
	print("\n== 躲藏")
	await to_lab()
	var patrol = main.patrols.get("guard")
	ok(patrol != null and not patrol.is_facing_right(), "設施走廊：警衛有巡視，一開始面向左")
	await walk_to(1150)
	await frames(5)
	ok(main.get("_gesture_hint").visible and main.get("_gesture_hint").text == "避開手電筒的光：靠近掩護按 E 躲起來", "走過 x 1100：畫面下方提示一次")
	await seconds(4.3)
	ok(patrol.is_facing_right(), "約 4 秒後轉身面向右")
	await seconds(3.2)
	ok(not patrol.is_facing_right(), "約 3 秒後轉回面向左")

	# 站在光裡 → 被發現
	patrol.face_toward(0.0)
	await place(1500, 692)
	await wait_for(func(): return main.state != EXPLORE, 2.0)
	ok(gs().has_flag("lab.guard.spotted") and main.sound_log.has("pickup_2.ogg"), "站在光照到的地方 0.4 秒：被發現（旗標、上膛聲）")
	ok(main.body.text.contains("誰在那裡"), "被發現：警衛事件換成「手電筒的光停在你身上……」")
	await choose(0)  # 抵抗成功後選「躲進通風管」
	ok(not figure_visible("Guard"), "警衛事件結束：警衛離開")
	await back_to_title()

	# 躲在箱子後面：光照到也不會被發現；一移動就出來
	await to_lab()
	patrol = main.patrols.get("guard")
	await place(1450, 660)
	ok(prompt().contains("躲起來"), "箱子：提示「E　躲起來」")
	await interact()
	ok(player().in_cover and main.sound_log.back() == "inspect_4.ogg" and prompt().contains("出來"), "按 E：躲到箱子後面（布料聲），提示變成「E　出來」")
	patrol.face_toward(0.0)
	await seconds(1.0)
	ok(main.state == EXPLORE and not gs().has_flag("lab.guard.spotted"), "躲著時警衛面向這裡、光照到：不會被發現")
	Input.action_press("move_left")
	await physics(6)
	Input.action_release("move_left")
	await physics(2)
	ok(not player().in_cover, "一移動就從掩護後面出來")

	# 通風管：從另一頭出來，警衛事件一起結束
	patrol.face_toward(2200.0)  # 警衛面向右（背對主角）
	await place(1545, 670)
	ok(prompt().contains("鑽進通風管"), "通風管入口：提示「E　鑽進通風管」")
	await interact()
	await read()
	await wait_for(func(): return main.state in [TYPING, AREA_TEXT], 4.0)
	ok(absf(px() - 1950.0) < 1.0 and main.body.text.contains("另一頭爬出來"), "從通風管另一頭（x 1950）爬出來，顯示爬出來的文字")
	ok(gs().has_flag("lab.guard") and not figure_visible("Guard"), "警衛事件算結束：警衛走遠、消失")
	await read()
	ok(main.state == EXPLORE and not patrol.active, "可以繼續走，警衛不再巡視")
	await go_exit(2150, "ruins")
	ok(area() == "ruins", "走到出口：進入廢墟")


func run_validation() -> void:
	print("\n== 劇本檢查")
	var story: StoryData = main.story
	ok(AreaData.gesture_errors(story, { "gesture": { "text": "有反應", "range": 300, "effects": { "memory": 1 } } }, "x").is_empty(), "正確的 gesture：通過")
	ok(AreaData.gesture_errors(story, { "gesture": "文字" }, "x").size() == 1, "gesture 不是物件：報錯")
	ok(AreaData.gesture_errors(story, { "gesture": { "text": "  " } }, "x").size() == 1, "gesture 沒有 text：報錯")
	ok(AreaData.gesture_errors(story, { "gesture": { "text": "a", "range": -5 } }, "x").size() == 1, "gesture.range 不是正數：報錯")
	ok(AreaData.gesture_errors(story, { "gesture": { "text": "a", "effects": { "courage": 1 } } }, "x").size() == 1, "gesture.effects 用到不存在的數值：報錯")
	var with_gesture := 0
	for area_id in main.areas.area_ids():
		for point in main.areas.get_area(area_id).get("points", {}).values():
			if point.has("gesture"):
				with_gesture += 1
	ok(with_gesture == 7 and not story.gesture_alone.is_empty(), "資料：7 個互動點有手勢反應，另有沒有對象時的獨白")
	ok(AreaData.flashback_errors({ "type": "inspect", "flashback": "scene_10.webp" }, "x").is_empty(), "正確的 flashback：通過")
	ok(AreaData.flashback_errors({ "type": "inspect", "flashback": "scene_99.webp" }, "x").size() == 1, "flashback 插畫不存在：報錯")
	ok(AreaData.flashback_errors({ "type": "exit", "flashback": "scene_10.webp" }, "x").size() == 1, "出口有 flashback：報錯")
	var two := [{ "text": "a" }, { "text": "b" }]
	ok(AreaData.resist_errors({ "type": "choice", "choices": two, "resist": { "presses": 10, "time": 5.0, "fail": 1 } }, "x").is_empty(), "正確的 resist：通過")
	ok(AreaData.resist_errors({ "type": "choice", "choices": two, "resist": { "presses": 10, "time": 5.0, "fail": 2 } }, "x").size() == 1, "resist.fail 指向不存在的選項：報錯")
	ok(AreaData.resist_errors({ "type": "choice", "choices": two, "resist": { "presses": 0, "time": -1, "fail": 0 } }, "x").size() == 2, "resist.presses、time 不是正數：報錯")
	ok(AreaData.resist_errors({ "type": "inspect", "resist": { "fail": 0 } }, "x").size() == 2, "不是 choice 卻有 resist：報錯")
	var lab: Dictionary = main.areas.get_area("lab")
	ok(AreaData.hide_errors(lab, lab["points"]["vent"], "x").is_empty() and AreaData.patrol_errors(lab["points"]["guard"], "x").is_empty(), "走廊的通風管、警衛巡視：通過")
	ok(AreaData.hide_errors(lab, { "type": "hide", "to_x": 1950, "done": "nobody" }, "x").size() == 3, "通風管沒有文字、done 指向不存在的互動點：報錯")
	ok(AreaData.patrol_errors({ "patrol": { "face_left": 0, "spot_time": -1 } }, "x").size() == 2, "patrol 的秒數不是正數：報錯")
