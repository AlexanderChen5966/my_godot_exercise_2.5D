## A2-4 鏡頭效果：人物事件時輕微推近、撲上去與槍聲時震動、衝動強度高時輕微晃動。掛在 Main 的 CameraFx 節點上。
## Main 換區域時用 set_camera() 指定鏡頭；視覺小說畫面沒有鏡頭，震動改成移動背景圖（set_background）。
## 強度都在下面的 @export，可以在編輯器的屬性面板直接調整。
extends Node

@export_group("推近")
## 人物事件時的鏡頭倍率（1 = 不推近）與推近、退回的時間（秒）
@export_range(1.0, 1.5, 0.01) var event_zoom := 1.12
@export var zoom_in_time := 0.8
@export var zoom_out_time := 0.6

@export_group("震動")
## 撲上去、槍聲時的最大位移（px）與持續時間（秒）；震動中每秒換幾次位置
@export var shake_strength := 18.0
@export var shake_time := 0.45
@export var shake_rate := 30.0

@export_group("晃動")
## 衝動強度超過 sway_from 才開始晃，最強時位移 sway_px（px）；sway_speed 是每秒幾個來回
@export_range(0.0, 1.0, 0.05) var sway_from := 0.3
@export var sway_px := 8.0
@export var sway_speed := 0.35

var sway := 0.0  # Main 每個畫面設定（衝動強度 0～1）

var _camera: Camera2D
## B1：3D 區域的鏡頭由 area_3d.gd 自己跟著主角，這裡只設定它的 camera_zoom（推近）與 camera_offset（震動、晃動，像素）
var _area_3d: Node
var _background: Control
var _zoom_tween: Tween
var _shake_left := 0.0
var _shake_strength_now := 0.0
var _shake_offset := Vector2.ZERO
var _shake_wait := 0.0
var _time := 0.0


## 換區域時指定鏡頭（沒有區域時傳 null）；鏡頭回到原本大小、不震動。3D 區域傳 Camera3D 和區域本身
func set_camera(camera: Node, area: Node = null) -> void:
	_camera = camera as Camera2D
	_area_3d = area if camera is Camera3D else null
	if is_instance_valid(_area_3d):
		_area_3d.camera_zoom = 1.0
		_area_3d.camera_offset = Vector2.ZERO
	_shake_left = 0.0
	_shake_offset = Vector2.ZERO
	if _zoom_tween:
		_zoom_tween.kill()
	if is_instance_valid(_camera):
		_camera.zoom = Vector2.ONE
		_camera.offset = Vector2.ZERO


## 視覺小說畫面震動時移動的背景圖
func set_background(background: Control) -> void:
	_background = background


## 人物事件開始：推近；事件結束：退回
## 鏡頭跟著主角（腳底），平常被區域下緣擋住；推近時下緣限制放寬，鏡頭自然往主角靠，人物在畫面上的高度幾乎不變
func push_in() -> void:
	_zoom_to(event_zoom, zoom_in_time)


func release() -> void:
	_zoom_to(1.0, zoom_out_time)


func shake(strength_scale := 1.0) -> void:
	_shake_left = shake_time
	_shake_wait = 0.0
	_shake_strength_now = shake_strength * strength_scale


func _zoom_to(value: float, time: float) -> void:
	if _zoom_tween:
		_zoom_tween.kill()
	if is_instance_valid(_area_3d):
		_zoom_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		_zoom_tween.tween_property(_area_3d, "camera_zoom", value, time)
		return
	if not is_instance_valid(_camera):
		return
	_zoom_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_zoom_tween.tween_property(_camera, "zoom", Vector2.ONE * value, time)


func _process(delta: float) -> void:
	_time += delta
	_update_shake(delta)
	var sway_offset := Vector2.ZERO
	var amount := clampf((sway - sway_from) / maxf(1.0 - sway_from, 0.01), 0.0, 1.0)
	if amount > 0.0:
		# 兩個不同頻率的正弦疊在一起，像手持鏡頭不規則地晃
		var t := _time * TAU * sway_speed
		sway_offset = Vector2(sin(t) + 0.5 * sin(t * 2.3 + 1.0), 0.6 * sin(t * 1.7 + 2.0)) * sway_px * amount
	var total := (_shake_offset + sway_offset).round()  # 整數像素，避免像素圖抖動時變模糊
	if is_instance_valid(_area_3d):
		_area_3d.camera_offset = total
	elif is_instance_valid(_camera):
		_camera.offset = _clamp_to_limits(total)
		if is_instance_valid(_background):
			_background.position = Vector2.ZERO
	elif is_instance_valid(_background):
		_background.position = _shake_offset.round()


func _update_shake(delta: float) -> void:
	if _shake_left <= 0.0:
		_shake_offset = Vector2.ZERO
		return
	_shake_left -= delta
	_shake_wait -= delta
	if _shake_wait <= 0.0:
		_shake_wait = 1.0 / shake_rate
		var fall := clampf(_shake_left / shake_time, 0.0, 1.0)  # 越來越小
		_shake_offset = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * _shake_strength_now * fall


## Camera2D 的 offset 不受 limit 限制：鏡頭貼在區域邊緣時往外震會露出區域外的灰色，所以自己限制在區域內
func _clamp_to_limits(want: Vector2) -> Vector2:
	var center := _camera.get_screen_center_position() - _camera.offset  # 不含 offset 的鏡頭中心
	var half := _camera.get_viewport_rect().size / 2.0 / _camera.zoom
	var lo := Vector2(_camera.limit_left, _camera.limit_top) + half - center
	var hi := Vector2(_camera.limit_right, _camera.limit_bottom) - half - center
	return Vector2(clampf(want.x, minf(lo.x, 0.0), maxf(hi.x, 0.0)), clampf(want.y, minf(lo.y, 0.0), maxf(hi.y, 0.0))).round()
