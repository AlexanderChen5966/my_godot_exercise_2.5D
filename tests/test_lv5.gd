## Lv5-6 自動測試：從停車場一路玩到牆前。
## 最佳路線 → 結局 A、一般路線 → B、最差路線 → C；三個 Bad End 重試都回到檢查點、數值還原；Bad End 回標題後重設。
## 共用操作在 play_base.gd。執行：zsh tests/run_tests.sh test_lv5
extends "res://tests/play_base.gd"

const INITIAL := { "memory": 0, "humanity": 3 }


func run_tests() -> void:
	await run_best()
	await back_to_title()
	await run_normal()
	await back_to_title()
	await run_worst()
	await back_to_title()
	await run_bad_ends()


## 最佳路線：每個能加記憶、人性的地方都選好的
func run_best() -> void:
	print("\n== 最佳路線 → 結局 A")
	await start_game()
	# 停車場
	await walk_to(300); await interact(); await read()          # 醒來的地方 記憶 +1
	await walk_to(1460); await choose(0)                        # 婦人：強行壓制自己 人性 +1
	await go_exit(2150, "street")
	await walk_to(1450); await interact(); await read()         # 尋人啟事 記憶 +1
	await go_exit(2150, "clinic")
	await walk_to(600); await interact(); await read()          # 藥櫃：錄音筆
	await walk_to(1750); await interact(); await choose(0)      # 坐下聽錄音 記憶 +1
	await walk_to(1300); await interact(); await read()         # 治療室 記憶 +1
	ok(gs().stats == { "memory": 4, "humanity": 4 }, "停車場～診所：記憶 4、人性 4")
	await exit_to_scene(2150, 6)
	await choose(0); await to_scene(7)                          # 舉起雙手 人性 +1
	await choose(0); await enter("lab")                         # 環顧四周 記憶 +1
	ok(area() == "lab", "手術台 → 設施走廊")
	await walk_to(700); await choose(0)                         # 收下筆記本 記憶 +1
	ok(gs().has_item("notebook"), "收下筆記本")
	await walk_to(1650); await choose(0)                        # 躲進通風管
	await go_exit(2150, "ruins")
	await walk_to(800); await choose(1)                         # 把他們引開 人性 +2
	await walk_to(1600); await choose(0)                        # 隔著圍籬看著她 記憶 +1
	await go_exit(2150, "home")
	ok(gs().stats == { "memory": 7, "humanity": 7 }, "設施走廊～廢墟：記憶 7、人性 7")
	await walk_to(600); await interact(); await read()          # 牆上的蠟筆字 記憶 +1
	await walk_to(1650)
	var girl: Node = main.get("_area").get_node("Points/Daughter/Figure")
	await wait_choices(); await select(0)                       # 比出手勢 記憶 +1、人性 +1
	ok(girl.animation == "wave", "比出手勢：女兒舉起小手比出同樣的手勢（A3）")
	await read()
	ok(girl.animation == "leave" and girl.visible, "事件結束：女兒轉身背對窗戶（還沒消失）")
	await wait_for(func(): return not girl.visible, 3.0)
	ok(not girl.visible, "女兒淡出後消失")
	ok(gs().has_flag("home.daughter#0"), "有筆記本：女兒用的是筆記本版本")
	await exit_to_scene(2150, 15)
	await choose(0); await enter("wall")                        # 營火 → 牆前
	ok(gs().stats == { "memory": 9, "humanity": 8 }, "到牆前：記憶 9、人性 8（最高）")
	await walk_to(1500); await interact(); await wait_choices()
	ok(not locked(0) and not locked(1) and not locked(2), "最後的動作：三個選項都能選")
	await choose(0); await to_scene(18)
	ok(main.current_id == 18, "面對真相 → 結局 A")


## 一般路線：只拿到一部分記憶，人性很低
func run_normal() -> void:
	print("\n== 一般路線 → 結局 B")
	await start_game()
	ok(gs().stats == INITIAL and gs().items.is_empty(), "回標題後重新開始：數值、物品重設")
	await walk_to(300); await interact(); await read()          # 記憶 +1
	await walk_to(1460); await choose(1)                        # 撲上去 人性 −1
	await go_exit(2150, "street")
	await go_exit(2150, "clinic")
	await exit_to_scene(2150, 6)
	await choose(1); await to_scene(7)                          # 拼命掙脫
	await choose(2); await enter("lab")                         # 拼命掙扎
	await walk_to(700)
	var sci: Node = main.get("_area").get_node("Points/Scientist/Figure")
	ok(sci.animation == "event", "女科學家：事件開始時遞出筆記本（A3 event 動畫）")
	await choose(1)                                             # 撲向科學家 人性 −2
	await physics(2)
	ok(sci.animation == "run" and sci.visible, "撲向科學家後她直接逃跑（沒有尖叫），還沒消失")
	ok(not gs().has_item("notebook"), "撲向科學家：沒有筆記本")
	await walk_to(1650)
	var guard: Node = main.get("_area").get_node("Points/Guard/Figure")
	var torch: Node = main.get("_area").get_node("Points/Guard/Torch")
	ok(guard.animation == "event" and torch_level_left(torch), "警衛：事件開始時舉槍瞄準，手電筒的光水平照過來（A3）")
	await choose(1)                                             # 撲向警衛 人性 −1
	await go_exit(2150, "ruins")
	await walk_to(800); await choose(2)                         # 躲起來
	await walk_to(1600); await choose(0)                        # 看著她 記憶 +1
	await go_exit(2150, "home")
	await walk_to(600); await interact(); await read()          # 記憶 +1
	await walk_to(1650); await choose(1)                        # 靠近她 人性 −1
	ok(gs().has_flag("home.daughter") and not gs().has_flag("home.daughter#0"), "沒有筆記本：女兒用的是一般版本")
	await exit_to_scene(2150, 15)
	await choose(1); await enter("wall")
	ok(gs().stats == { "memory": 3, "humanity": -2 }, "到牆前：記憶 3、人性 −2")
	await walk_to(1500); await interact(); await wait_choices()
	ok(locked(0) and not locked(1) and not locked(2), "最後的動作：面對真相鎖住，沉浸幻象、永遠遊走能選")
	ok((main.choices_box.get_child(0) as Button).text == "……（你想不起來）", "鎖住的選項顯示「……（你想不起來）」")
	await choose(1); await to_scene(19)
	ok(main.current_id == 19, "沉浸幻象 → 結局 B")


## 最差路線：什麼都不調查，直接走到底
func run_worst() -> void:
	print("\n== 最差路線 → 結局 C")
	await start_game()
	await go_exit(2150, "street")
	await go_exit(2150, "clinic")
	await exit_to_scene(2150, 6)
	await choose(1); await to_scene(7)
	await choose(2); await enter("lab")
	await go_exit(2150, "ruins")
	await go_exit(2150, "home")
	await exit_to_scene(2150, 15)
	await choose(2); await enter("wall")
	ok(gs().stats == INITIAL, "到牆前：數值還是初始值")
	await walk_to(1500); await interact(); await wait_choices()
	ok(locked(0) and locked(1) and not locked(2), "最後的動作：只剩永遠遊走能選")
	await choose(2); await to_scene(20)
	ok(main.current_id == 20, "永遠遊走 → 結局 C")


## 三個 Bad End：重試回到檢查點（進入區域或過場時），數值與物品還原成那時候的樣子
func run_bad_ends() -> void:
	print("\n== Bad End 與重試")
	await start_game()
	await walk_to(300); await interact(); await read()          # 記憶 +1（檢查點之前）
	await go_exit(2150, "street")
	await go_exit(2150, "clinic")
	await exit_to_scene(2150, 6)
	var at_scene6: Dictionary = gs().stats.duplicate()
	await choose(2); await to_scene(21)                         # 狂吼嘶吼
	ok(main.current_id == 21, "搜捕隊：狂吼嘶吼 → BE1 槍聲")
	await end_choice(0); await to_scene(6)
	ok(main.current_id == 6 and gs().stats == at_scene6 and gs().stats["memory"] == 1, "BE1 重試：回到搜捕隊，數值是進場時的值（記憶 1 保留）")

	await choose(0); await to_scene(7)                          # 舉起雙手 人性 +1
	await choose(0); await enter("lab")                         # 記憶 +1
	var at_lab: Dictionary = gs().stats.duplicate()
	await walk_to(700); await choose(0)                         # 收下筆記本 記憶 +1
	await walk_to(1650); await choose(2); await to_scene(22)    # 停下不動
	ok(main.current_id == 22, "警衛：停下不動 → BE2 編號 07")
	await end_choice(0); await enter("lab")
	ok(area() == "lab" and gs().stats == at_lab, "BE2 重試：回到設施走廊，數值還原")
	ok(not gs().has_item("notebook") and figure_visible("Scientist"), "BE2 重試：筆記本收回、女科學家重新出現")

	await walk_to(700); await choose(0)                         # 再收一次筆記本
	ok(gs().has_item("notebook") and gs().stats["memory"] == at_lab["memory"] + 1, "重試後可以再收下筆記本（記憶 +1 再算一次）")
	await walk_to(1650); await choose(0)
	await go_exit(2150, "ruins")
	var at_ruins: Dictionary = gs().stats.duplicate()
	await walk_to(800); await choose(1)                         # 引開 人性 +2
	await walk_to(1600); await choose(2); await to_scene(23)    # 撲向她
	ok(main.current_id == 23, "妻子：撲向她 → BE3 噬語")
	await end_choice(0); await enter("ruins")
	ok(area() == "ruins" and gs().stats == at_ruins and figure_visible("Horde"), "BE3 重試：回到廢墟，人性還原、同類重新出現")
	ok(gs().has_item("notebook"), "BE3 重試：檢查點之前拿到的筆記本還在")

	await walk_to(1600); await choose(2); await to_scene(23)
	await end_choice(1)
	await wait_for(func(): return main.state == TITLE, 5.0)
	ok(main.state == TITLE, "Bad End 選回到標題 → 標題畫面")
	await start_game()
	ok(gs().stats == INITIAL and gs().items.is_empty() and gs().flags.is_empty(), "重新開始：數值、物品、旗標都重設")


## 警衛的手電筒水平往左照（2D：PointLight2D 轉 180 度；3D：聚光燈的 −Z 朝 −X）
func torch_level_left(torch: Node) -> bool:
	if torch is Node3D:
		var dir: Vector3 = -torch.global_transform.basis.z
		return dir.x < -0.99 and absf(dir.y) < 0.01
	return is_equal_approx(torch.rotation, PI)
