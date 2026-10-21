## Lv4-7 自動測試：停車場 → 街道 → 診所，跑三輪（不拿錄音筆／拿錄音筆／回標題重設）。
## 共用操作在 play_base.gd。執行：zsh tests/run_tests.sh test_lv4
extends "res://tests/play_base.gd"


func run_tests() -> void:
	await run_a()
	await run_b()
	await run_c()


# ---- 三輪 ----

## A：不拿錄音筆，診療椅只有描述
func run_a() -> void:
	print("\n== A：不拿錄音筆")
	await start_game()
	ok(area() == "parking_lot" and gs().stats == { "memory": 0, "humanity": 3 }, "從停車場開始，數值是初始值")
	await walk_to(300); await interact(); await read()
	ok(gs().stats["memory"] == 1, "醒來的地方：記憶 +1")
	await walk_to(300); await interact(); await read()
	ok(gs().stats["memory"] == 1, "同一處再調查：記憶不再增加")
	await walk_to(1460)                       # 婦人：走近自動觸發
	await choose(0)                           # 強行壓制自己
	ok(gs().stats["humanity"] == 4, "婦人選「強行壓制自己」：人性 +1")
	var woman: Node = main.get("_area").get_node("Points/Woman/Figure")
	var start_x: float = woman.position.x
	ok(woman.visible and woman.animation == "scream", "婦人事件後先尖叫（A3），還沒消失")
	await wait_for(func(): return woman.animation == "run", 2.0)
	await physics(10)
	ok(woman.flip_h and woman.position.x > start_x, "婦人往遠離主角的方向（右）跑")
	await wait_for(func(): return not woman.visible, 6.0)
	ok(not figure_visible("Woman"), "婦人跑出畫面後消失")
	await go_exit(2150, "street")
	ok(is_equal_approx(px(), 220), "進街道出現在 x=220")
	await walk_to(1450); await interact(); await read()
	ok(gs().stats["memory"] == 2, "尋人啟事：記憶 +1")
	await go_exit(2150, "clinic")
	await walk_to(1750); await interact(); await read()
	ok(gs().has_flag("clinic.chair") and not gs().has_flag("clinic.chair#0"), "沒錄音筆時坐診療椅：只有描述")
	await go_exit(70, "street")
	ok(is_equal_approx(px(), 2100) and player().facing == -1, "回街道出現在右邊（x=2100）、面向左")
	await go_exit(2150, "clinic")
	ok(main.get("_closing_point") == "" and main.state == EXPLORE, "第二次進診所：不再顯示開場")
	await walk_to(2150); await interact(); await read(); await wait_for(func(): return main.current_id == 6, 6.0)
	ok(main.current_id == 6 and area() == "", "離開診所：接到場景 6（搜捕隊）")
	ok(gs().stats == { "memory": 2, "humanity": 4 } and gs().items.is_empty(), "A 結束：記憶 2、人性 4、沒有物品")


## B：拿錄音筆再坐診療椅
func run_b() -> void:
	print("\n== B：拿錄音筆")
	await back_to_title()
	await start_game()
	await walk_to(1460); await choose(1)      # 撲上去
	ok(gs().stats["humanity"] == 2, "婦人選「撲上去」：人性 −1")
	await go_exit(2150, "street")
	await go_exit(2150, "clinic")
	await walk_to(1750); await interact(); await read()       # 先坐（還沒錄音筆）
	await walk_to(600); await interact(); await read()
	ok(gs().has_item("recorder") and not figure_visible("Cabinet"), "藥櫃：得到錄音筆、櫃上的錄音筆消失")
	await walk_to(1750)
	ok(prompt() == "E　坐下", "有錄音筆後，診療椅的提示變成「坐下」")
	await interact(); await choose(0)         # 反覆播放
	ok(gs().stats["memory"] == 1, "坐下聽錄音（反覆播放）：記憶 +1")
	await walk_to(1300); await walk_to(1750)
	ok(not main.prompt_label.visible, "聽過錄音後，診療椅不再反應")
	await walk_to(1300); await interact(); await read()
	ok(gs().stats["memory"] == 2, "治療室：記憶 +1")
	ok(gs().stats == { "memory": 2, "humanity": 2 }, "B 結束：記憶 2、人性 2")


## C：回標題再玩一輪，狀態全部重設
func run_c() -> void:
	print("\n== C：回標題再玩一輪")
	await back_to_title()
	ok(main.state == TITLE, "回到標題畫面")
	await start_game(false)
	ok(main.state == AREA_TEXT or main.state == TYPING, "新的一輪：停車場開場再次顯示")
	await read()
	ok(gs().stats == { "memory": 0, "humanity": 3 } and gs().items.is_empty() and gs().flags.is_empty(), "數值、物品、旗標都重設")
	ok(figure_visible("Woman"), "婦人重新出現")
	await walk_to(300); await interact(); await read()
	ok(gs().stats["memory"] == 1, "重設後同一處可以再加記憶")
