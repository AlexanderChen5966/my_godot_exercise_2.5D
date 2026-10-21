## A4 自動測試：音量分組、環境音、腳步聲跟著行走畫格、互動／事件／介面音、位置音效、燈管熄滅時嗡聲靜音、Bad End 音樂與槍聲、資料檢查。
## 共用操作在 play_base.gd。執行：zsh tests/run_tests.sh test_a4
## （headless 沒有實際輸出聲音：這裡檢查的是「在正確時機播放了哪個聲音」，好不好聽由作者判斷）
extends "res://tests/play_base.gd"


func run_tests() -> void:
	run_setup()
	await run_parking()
	await run_street_and_bad_end()
	await back_to_title()
	ok(main.get("_bgm_file") == "bgm_title.ogg", "回到標題：播放新的標題曲 bgm_title")
	ok(main.get("_amb_file") == "", "回到標題：環境音淡出")
	run_validation()


## 音量分組與 Main 的播放器
func run_setup() -> void:
	print("\n== 音量分組")
	for bus in ["BGM", "SFX", "Ambient"]:
		ok(AudioServer.get_bus_index(bus) > 0, "有音量分組 %s" % bus)
	ok(main.get_node("%BgmA").bus == &"BGM" and main.get_node("%AmbA").bus == &"Ambient" and main.get_node("%Sfx").bus == &"SFX", "BGM／環境音／音效的播放器分到各自的分組")
	var heartbeat := main.impulse_fx.get_node("Heartbeat") as AudioStreamPlayer
	ok(heartbeat.stream.resource_path.ends_with("heartbeat.ogg") and main.impulse_fx.sample_has_two_beats, "心跳換成新的錄音（一組兩拍，程式不再補第二聲）")


func run_parking() -> void:
	print("\n== 停車場")
	await start_game()
	ok(main.get("_amb_file") == "amb_parking.ogg" and ((main.get_node("%AmbA") as AudioStreamPlayer).playing or (main.get_node("%AmbB") as AudioStreamPlayer).playing), "進入停車場：播放 amb_parking")
	ok(player().step_sounds.size() == 3 and player().step_sounds[0].resource_path.contains("step_concrete"), "停車場的地面是水泥：3 個水泥腳步聲")
	var steps: int = player().steps_played
	await hold("move_right", 60)
	var walked: int = player().steps_played - steps
	ok(walked >= 2 and walked <= 4, "走 1 秒（行走 8 fps，每 6 格踩 2 步）：腳步聲 %d 次" % walked)
	await hold("move_right", 2)
	steps = player().steps_played
	await physics(40)
	ok(player().steps_played == steps, "站著不動：沒有腳步聲")
	ok(not (player().get_node("Steps") as AudioStreamPlayer).playing, "停下來：正在播的腳步聲很快淡出（A4-3）")

	# 位置音效：燈管嗡聲，熄滅時靜音並播一次喀喀聲
	var hum: Node = main._area.get_node("Points/Light/Hum")      # AudioStreamPlayer2D 或 3D
	var flicker: Node = main._area.get_node("Points/Light/Flicker")
	ok(hum.playing and hum.bus == &"Ambient", "燈管的嗡聲是位置音效、自動播放")
	var lamp: Node = main._area.get_node("Lights/LampLight" if is_3d() else "LampLight")
	var chance: float = lamp.get("dropout_chance")
	lamp.set("_since_sound", 99.0)  # 遊戲剛開始時燈管可能已經自己熄滅過一次，喀喀聲還在冷卻；先歸零，測試才穩定
	lamp.set("dropout_chance", 1.0)
	await frames(3)
	ok(hum.volume_db <= -79.0 and flicker.playing, "燈管熄滅：嗡聲靜音，播放啟動器的喀喀聲")
	lamp.set("dropout_chance", chance)
	await wait_for(func(): return hum.volume_db > -79.0, 2.0)
	ok(hum.volume_db > -79.0, "燈管亮回來：嗡聲恢復")

	await walk_to(1000); await interact()
	ok(main.sound_log.back() == "inspect", "調查地面殘骸：翻找聲")
	await frames(20)
	ok(main.state == TYPING and not main.type_sfx.playing, "打字中沒有打字聲（A4-3：和音效重疊太躁，先關掉）")
	await read()

	# 婦人：抵抗失敗 → 自動撲上去（低吼，沒有確認音）；逃走時尖叫（A5 起婦人的事件先抵抗衝動）
	await walk_to(1460)
	await wait_choices()
	main.call("_finish_resist", false)
	ok(main.sound_log.back() == "growl" and not main.sound_log.has("ui_confirm"), "抵抗失敗、自動撲上去：低吼（不是自己選的，沒有確認音）")
	await read()
	ok(main.sound_log.back() == "scream", "婦人逃走：尖叫")


func run_street_and_bad_end() -> void:
	print("\n== 街道、診所、Bad End")
	await walk_to(2150); await interact(); await read()   # 關閉出口文字時通過出口
	var opened := Time.get_ticks_msec()
	ok(main.sound_log.back() == "door_metal", "離開停車場：推開鐵門")
	await wait_for(func(): return area() == "street", 4.0)
	var black := (Time.get_ticks_msec() - opened) / 1000.0
	ok(black >= 0.8, "開門聲後在黑畫面停一下才進街道（%.2f 秒，A4-3）" % black)
	await enter("street")
	ok(main.get("_amb_file") == "amb_street.ogg", "進入街道：環境音換成 amb_street")
	ok(player().step_sounds[0].resource_path.contains("step_glass"), "街道的地面是碎玻璃")
	var fire: Node = main._area.get_node("Points/Car/Fire")
	ok(fire.playing and audio_range(fire) >= 800.0, "燃燒的車：火聲是位置音效")
	await go_exit(2150, "clinic")
	ok(main.sound_log.back() == "door_wood", "走進診所：木門")
	await walk_to(600); await interact()
	ok(main.sound_log.back() == "pickup", "撿起錄音筆：撿起的聲音")
	await read()
	await walk_to(2150); await interact(); await read()
	await to_scene(6)
	ok(main.get("_amb_file") == "", "過場（搜捕隊）：環境音淡出")
	await wait_choices()
	ok(not main.sound_log.has("ui_cursor"), "選項出現、自動選好第一個：沒有游標聲")
	await select(2)
	ok(main.sound_log.has("ui_cursor") and main.sound_log.has("ui_confirm"), "方向鍵移動有游標聲，按下有確認音")
	await read()
	await wait_for(func(): return main.sound_log.back() == "gunshot", 3.0)
	ok(main.sound_log.back() == "gunshot" and main.fade.color.a > 0.9 and main.get("_bgm_file") == "bgm_bad.ogg", "Bad End「槍聲」：槍聲在黑畫面中響起（A4-3），Bad End 音樂 bgm_bad")


## 資料檢查：音效名稱找得到檔案；隨機變化
func run_validation() -> void:
	print("\n== 資料檢查")
	ok(SoundLib.variants("growl").size() == 2 and SoundLib.variants("step_wood").size() == 3, "growl 有 2 個變化、step_wood 有 3 個")
	ok(SoundLib.paths("fence") == ["res://assets/sfx/fence.ogg"], "沒有編號的音效（fence）用 fence.ogg")
	ok(AreaData.sound_errors({ "sfx": "growl", "done_sfx": "scream" }, "x").is_empty(), "存在的音效：檢查通過")
	ok(AreaData.sound_errors({ "sfx": "no_such_sound" }, "x").size() == 1, "不存在的音效：劇本檢查會報錯")
	ok(AreaData.sound_errors({ "sfx": ["growl", "scream"] }, "x").is_empty() and AreaData.sound_errors({ "sfx": ["growl", "nope"] }, "x").size() == 1, "音效可以寫成陣列（撲向妻子：低吼＋尖叫），每個都會檢查")


func hold(action: String, physics_frames: int) -> void:
	Input.action_press(action)
	await physics(physics_frames)
	Input.action_release(action)
	await physics(2)
