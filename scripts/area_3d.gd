## 3D 版可走動區域的根節點（B1，所有 3D 區域共用；範本 scenes/areas3d/AreaBase3D.tscn）。
## 和 2D 版 area.gd 一樣的介面：設定玩家起點、移動範圍與鏡頭，並把互動點的訊號轉給 Main。
## 區域資料（data/areas/*.json）維持 2D 的像素座標，這裡換算：x 64 像素＝1 公尺；
## 縱深帶 walk_top～walk_bottom（像素的 y）對應 z −depth/2（後）～＋depth/2（前）。
## 鏡頭只跟著 X 走、兩端不超出區域，往下看 tilt 度（B0 選的「接受縮放」做法）。
extends Node3D

signal point_entered(point_id: String)   # 玩家走進互動點範圍
signal point_exited(point_id: String)    # 玩家離開互動點範圍

const PX_PER_M := 64.0
const SCREEN_HEIGHT := 768.0

@export var area_width := 2304.0  # 像素（和 2D 版相同）
@export var player_start := Vector2(160, 692)
@export var edge_margin := 16.0  # 主角半寬（像素），避免身體超出區域邊緣
## 縱深帶：2D 版主角的腳可以走的 y 範圍（像素），在 3D 對應前後 depth 公尺
@export var walk_top := 650.0
@export var walk_bottom := 735.0
@export var depth := 3.0

@export_group("鏡頭")
@export var camera_fov := 40.0
@export var camera_distance := 14.3  # 公尺：縱深帶中間的主角在畫面上 96 像素高（和 2D 版一樣）
@export var camera_look := 4.55      # 鏡頭看的高度（公尺），讓主角的腳約在畫面 y 690
@export var camera_tilt := 12.0      # 往下看的角度

@export_group("光影")
## 主角身上的光（手電筒）的亮度與範圍；衝動機制的閃爍以 flashlight_energy 為基準（Main 傳給 impulse_fx）
@export var flashlight_energy := 0.6
@export var flashlight_range := 6.0

@export_group("灰盒")
## Geometry 底下沒有東西時，自動放地面和後牆（B1 的灰盒；B2 起換成真的模型後就不會再放）
@export var auto_graybox := true
@export var graybox_color := Color(0.45, 0.45, 0.47)

## 鏡頭效果（camera_fx.gd 設定）：推近倍率（1 = 不推近）與畫面位移（像素，震動、晃動）
var camera_zoom := 1.0
var camera_offset := Vector2.ZERO

@onready var player: CharacterBody3D = $Player
@onready var camera: Camera3D = $Camera
@onready var _dof: ShaderMaterial = $Camera/Dof.material_override if has_node("Camera/Dof") else null


func _ready() -> void:
	player.min_x = edge_margin / PX_PER_M
	player.max_x = (area_width - edge_margin) / PX_PER_M
	player.min_z = -depth / 2.0
	player.max_z = depth / 2.0
	player.position = Vector3(player_start.x / PX_PER_M, 0.0, 0.0)
	if has_node("Player/Flashlight"):
		$Player/Flashlight.light_energy = flashlight_energy
		$Player/Flashlight.omni_range = flashlight_range
	if auto_graybox and has_node("Geometry") and $Geometry.get_child_count() == 0:
		_build_graybox()
	camera.make_current()
	# 位置音效以主角為聽者（和 2D 版的鏡頭在主角身上一樣）；鏡頭離場景十幾公尺，用鏡頭當聽者會超出音效的範圍
	if has_node("Player/Listener"):
		$Player/Listener.make_current()
	_update_camera()
	if has_node("Points"):
		for point in $Points.get_children():
			if point.has_signal("player_entered"):
				point.player_entered.connect(func(id: String) -> void: point_entered.emit(id))
				point.player_exited.connect(func(id: String) -> void: point_exited.emit(id))


func _process(_delta: float) -> void:
	_update_camera()


## 像素 → 公尺（x）；像素的 y（縱深帶）→ z
func px_to_x(x: float) -> float:
	return x / PX_PER_M


func y_to_z(y: float) -> float:
	return lerpf(-depth / 2.0, depth / 2.0, inverse_lerp(walk_top, walk_bottom, y))


func z_to_y(z: float) -> float:
	return lerpf(walk_top, walk_bottom, inverse_lerp(-depth / 2.0, depth / 2.0, z))


## 主角的 x、y（像素，和 2D 版的 player.position 相同的意義）
func player_x() -> float:
	return player.position.x * PX_PER_M


func player_y() -> float:
	return z_to_y(player.position.z)


## 主角頭頂在畫面上的位置（像素），提示文字放在這上面
func player_head_screen() -> Vector2:
	return camera.unproject_position(player.global_position + Vector3(0.0, 1.5, 0.0))


## 換區域時的出現位置：放到 x（有給 y 時也放到 y，否則前後不變；剛進區域時在縱深帶中間），靠近右半邊時面向左（從右邊的出口進來）。
func place_player(x: float, y := NAN) -> void:
	player.position.x = clampf(x / PX_PER_M, player.min_x, player.max_x)
	if not is_nan(y):
		player.position.z = clampf(y_to_z(y), player.min_z, player.max_z)
	player.face(-1 if x > area_width / 2.0 else 1)
	_update_camera()  # 鏡頭直接跳到新位置


func set_can_move(value: bool) -> void:
	player.can_move = value


## A3：調查互動點時，主角轉向它並伸手
func player_reach(point_id: String) -> void:
	player.reach_toward(point_x(point_id))


## 互動點的節點（找不到時回傳 null）
func point_node(point_id: String) -> Node3D:
	for point in $Points.get_children():
		if point.get("point_id") == point_id:
			return point
	return null


## 互動點在區域裡的 x 座標（像素，衝動機制算距離用）；找不到時回傳 NAN。
func point_x(point_id: String) -> float:
	var point := point_node(point_id)
	return point.position.x * PX_PER_M if point else NAN


## 事件開始／結束時通知互動點（人物換成 event／idle 動畫，A3）
func point_event(point_id: String, started: bool) -> void:
	var point := point_node(point_id)
	if point and point.has_method("on_event_start"):
		if started:
			point.on_event_start()
		else:
			point.on_event_end()


## 選項指定的人物動畫（資料的 "figure"）
func point_play(point_id: String, anim: String) -> void:
	var point := point_node(point_id)
	if point and point.has_method("play_figure"):
		point.play_figure(anim)


## flee_from_x（像素）：事件剛結束時傳主角的 x，人物會先逃跑再消失（A3）；不傳時直接隱藏。
func consume_point(point_id: String, flee_from_x := NAN) -> void:
	var point := point_node(point_id)
	if point and point.has_method("consume"):
		point.consume(flee_from_x)


## 鏡頭只跟著 X 走，兩端不超出區域；前後（Z）固定在縱深帶中間。景深的焦點對在主角身上。
func _update_camera() -> void:
	var fov := camera_fov / camera_zoom
	var half_width := tan(deg_to_rad(fov) / 2.0) * camera_distance * get_viewport().get_visible_rect().size.aspect()
	var width_m := area_width / PX_PER_M
	var x := clampf(player.position.x, half_width, width_m - half_width) if width_m > half_width * 2.0 else width_m / 2.0
	var tilt := deg_to_rad(camera_tilt)
	var target := Vector3(x, camera_look, 0.0)
	camera.fov = fov
	camera.position = target + Vector3(0.0, sin(tilt), cos(tilt)) * camera_distance
	camera.rotation = Vector3(-tilt, 0.0, 0.0)
	# 震動、晃動：畫面位移（像素）換成鏡頭的位移（在主角那個距離上，畫面高 SCREEN_HEIGHT 像素）
	var m_per_px := 2.0 * camera_distance * tan(deg_to_rad(fov) / 2.0) / SCREEN_HEIGHT
	camera.h_offset = -camera_offset.x * m_per_px
	camera.v_offset = camera_offset.y * m_per_px
	if _dof:
		var focus := -(camera.global_transform.affine_inverse() * (player.global_position + Vector3(0.0, 0.75, 0.0))).z
		_dof.set_shader_parameter("focus_distance", focus)


## B1 灰盒：地面（比區域寬一些、前後 16 公尺）和後牆（縱深帶後面 2.7 公尺、高 16 公尺）
func _build_graybox() -> void:
	var width := area_width / PX_PER_M
	var material := StandardMaterial3D.new()
	material.albedo_color = graybox_color
	material.roughness = 0.9
	for part in [["Floor", Vector3(width + 8.0, 0.2, 16.0), Vector3(width / 2.0, -0.1, 1.0)],
			["BackWall", Vector3(width + 8.0, 16.0, 0.4), Vector3(width / 2.0, 8.0, -depth / 2.0 - 2.7)]]:
		var mesh := BoxMesh.new()
		mesh.size = part[1]
		var node := MeshInstance3D.new()
		node.name = part[0]
		node.mesh = mesh
		node.material_override = material
		node.position = part[2]
		$Geometry.add_child(node)
