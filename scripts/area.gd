## 可走動區域的根節點（所有區域共用）：設定玩家起點、移動範圍與鏡頭範圍，並把互動點的訊號轉給 Main。
extends Node2D

signal point_entered(point_id: String)   # 玩家走進互動點範圍
signal point_exited(point_id: String)    # 玩家離開互動點範圍

@export var area_width := 2304.0
@export var area_height := 768.0
@export var player_start := Vector2(160, 640)
@export var edge_margin := 16.0  # 主角色塊半寬，避免身體超出區域邊緣
## 縱深帶（A1.5）：主角的腳可以走的 y 範圍。進入區域時站在中間。
@export var walk_top := 650.0
@export var walk_bottom := 735.0

@export_group("景深（視差）")
## 各層相對鏡頭的移動倍率：小於 1 越遠、越慢；大於 1 越近、越快。區域裡沒有該層時忽略。
@export var far_scroll := 0.3
@export var mid_scroll := 0.7
@export var front_scroll := 1.3

@export_group("光影")
## 世界整體亮度（CanvasModulate）。0 = 全黑、1 = 原本亮度。UI 不受影響。
@export_range(0.0, 1.0, 0.01) var world_brightness := 0.32
## 手電筒光暈的大小倍率與亮度。
@export_range(0.1, 4.0, 0.05) var flashlight_scale := 1.5
@export_range(0.0, 4.0, 0.05) var flashlight_energy := 1.6
## 手電筒的高度（A2：人物有法線貼圖，高度 0 等於從身體裡照出來，正面會變暗）。
@export_range(0.0, 200.0, 1.0) var flashlight_height := 80.0
## 出口附近紅色警示燈的亮度與呼吸速度（RedLight）。
## 2D 燈光是「燈色 × 表面顏色」：停車場是暗青色，紅色成分少，所以紅燈的亮度要比手電筒高很多才看得見。
@export_range(0.0, 10.0, 0.1) var red_light_energy := 5.0
@export_range(0.1, 6.0, 0.1) var red_light_speed := 1.6

const PLAYER_HEIGHT := 96.0  # 主角畫面上的高度（32×48 放大 2 倍）

@onready var player: CharacterBody2D = $Player
@onready var camera: Camera2D = $Player/Camera2D


func _ready() -> void:
	player.min_x = edge_margin
	player.max_x = area_width - edge_margin
	player.min_y = walk_top
	player.max_y = walk_bottom
	player.position = Vector2(player_start.x, (walk_top + walk_bottom) / 2.0)
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = int(area_width)
	camera.limit_bottom = int(area_height)
	camera.make_current()
	_apply_parallax()
	_apply_lighting()
	if has_node("Points"):
		for point in $Points.get_children():
			if point.has_signal("player_entered"):
				point.player_entered.connect(func(id: String) -> void: point_entered.emit(id))
				point.player_exited.connect(func(id: String) -> void: point_exited.emit(id))


func _apply_parallax() -> void:
	for pair in [["FarLayer", far_scroll], ["MidLayer", mid_scroll], ["FrontLayer", front_scroll]]:
		if has_node(pair[0]):
			get_node(pair[0]).scroll_scale = Vector2(pair[1], 1.0)


func _apply_lighting() -> void:
	if has_node("Darkness"):
		$Darkness.color = Color(world_brightness, world_brightness, world_brightness * 1.08)
	if has_node("Player/Flashlight"):
		$Player/Flashlight.texture_scale = flashlight_scale
		$Player/Flashlight.energy = flashlight_energy
		$Player/Flashlight.height = flashlight_height
	if has_node("RedLight"):
		$RedLight.base_energy = red_light_energy
		$RedLight.pulse_speed = red_light_speed


## 主角的 x、y（像素）；3D 版 area_3d.gd 有同名的函式，Main 只透過這些讀主角的位置
func player_x() -> float:
	return player.position.x


func player_y() -> float:
	return player.position.y


## 主角頭頂在畫面上的位置（像素），提示文字放在這上面
func player_head_screen() -> Vector2:
	return player.get_global_transform_with_canvas().origin - Vector2(0.0, PLAYER_HEIGHT)


## 換區域時的出現位置：放到 x（有給 y 時也放到 y，否則留在縱深帶中間），靠近右半邊時面向左（從右邊的出口進來）。
func place_player(x: float, y := NAN) -> void:
	player.position.x = clampf(x, player.min_x, player.max_x)
	if not is_nan(y):
		player.position.y = clampf(y, player.min_y, player.max_y)
	player.face(-1 if x > area_width / 2.0 else 1)
	camera.force_update_scroll()
	camera.reset_smoothing()  # 鏡頭直接跳到新位置，不從起點滑過去


func set_can_move(value: bool) -> void:
	player.can_move = value


## A3：調查互動點時，主角轉向它並伸手
func player_reach(point_id: String) -> void:
	player.reach_toward(point_x(point_id))


## 互動點的節點（找不到時回傳 null）
func point_node(point_id: String) -> Node2D:
	for point in $Points.get_children():
		if point.get("point_id") == point_id:
			return point
	return null


## 互動點在區域裡的 x 座標（衝動機制算距離用）；找不到時回傳 NAN。
func point_x(point_id: String) -> float:
	for point in $Points.get_children():
		if point.get("point_id") == point_id:
			return (point as Node2D).position.x
	return NAN


## 事件開始／結束時通知互動點（人物換成 event／idle 動畫，A3）
func point_event(point_id: String, started: bool) -> void:
	for point in $Points.get_children():
		if point.get("point_id") == point_id and point.has_method("on_event_start"):
			if started:
				point.on_event_start()
			else:
				point.on_event_end()


## 選項指定的人物動畫（資料的 "figure"）
func point_play(point_id: String, anim: String) -> void:
	for point in $Points.get_children():
		if point.get("point_id") == point_id and point.has_method("play_figure"):
			point.play_figure(anim)


## flee_from_x：事件剛結束時傳主角的 x，人物會先逃跑再消失（A3）；不傳時直接隱藏。
func consume_point(point_id: String, flee_from_x := NAN) -> void:
	for point in $Points.get_children():
		if point.get("point_id") == point_id and point.has_method("consume"):
			point.consume(flee_from_x)
