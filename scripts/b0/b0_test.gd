## B0-1 技術驗證：灰盒停車場的鏡頭跟隨、兩種縱深帶做法切換、效能顯示。
## 按鍵：1 = 做法 A（接受縮放）、2 = 做法 B（縮小縱深帶）、3 = 陰影開關、4 = 人物受光開關
extends Node3D

const AREA_WIDTH := 36.0  # 2D 版 2304 螢幕像素 ÷ 64
const TILT_DEG := 12.0    # 往下看的角度
## 做法 A：鏡頭近、視角寬，縱深帶 3 公尺 → 人物前後大小差得多
## 做法 B：鏡頭遠、視角窄，縱深帶 0.8 公尺 → 人物大小幾乎不變
## distance、look（鏡頭看的高度）讓縱深帶中間的主角和 2D 版一樣大（96 像素）、腳下約在畫面 y 690
const MODES := {
	1: {"name": "A 接受縮放", "fov": 40.0, "distance": 14.3, "look": 4.55, "min_z": -1.5, "max_z": 1.5},
	2: {"name": "B 縮小縱深帶", "fov": 20.0, "distance": 31.4, "look": 4.65, "min_z": -0.4, "max_z": 0.4},
}

var mode := 1

@onready var player: CharacterBody3D = $Player
@onready var camera: Camera3D = $Camera
@onready var hud: Label = $Hud/Info
@onready var shadow_light: Light3D = $Lights/KeyLight


func _ready() -> void:
	set_mode(mode)


func set_mode(value: int) -> void:
	mode = value
	var m: Dictionary = MODES[mode]
	camera.fov = m.fov
	player.min_z = m.min_z
	player.max_z = m.max_z
	player.position.z = clampf(player.position.z, m.min_z, m.max_z)
	_update_camera()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event.is_pressed() or event.is_echo():
		return
	match (event as InputEventKey).physical_keycode:
		KEY_1:
			set_mode(1)
		KEY_2:
			set_mode(2)
		KEY_3:
			shadow_light.shadow_enabled = not shadow_light.shadow_enabled
		KEY_4:
			player.sprite.shaded = not player.sprite.shaded


func _process(_delta: float) -> void:
	_update_camera()
	hud.text = "FPS %d ｜ 做法 %s ｜ 陰影 %s ｜ 人物受光 %s ｜ draw calls %d\n主角 x %.2f z %.2f ｜ 1/2 切換做法、3 陰影、4 受光" % [
		Engine.get_frames_per_second(), MODES[mode].name,
		"開" if shadow_light.shadow_enabled else "關", "開" if player.sprite.shaded else "關",
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		player.position.x, player.position.z]


## 鏡頭只跟著 X 走，兩端不超出區域；前後（Z）固定在縱深帶中間。
func _update_camera() -> void:
	var m: Dictionary = MODES[mode]
	var half_width: float = tan(deg_to_rad(m.fov) / 2.0) * m.distance * get_viewport().get_visible_rect().size.aspect()
	var x := clampf(player.position.x, half_width, AREA_WIDTH - half_width)
	var target := Vector3(x, m.look, (m.min_z + m.max_z) / 2.0)
	var tilt := deg_to_rad(TILT_DEG)
	camera.position = target + Vector3(0.0, sin(tilt), cos(tilt)) * m.distance
	camera.rotation = Vector3(-tilt, 0.0, 0.0)
