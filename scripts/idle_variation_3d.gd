## B1：idle_variation.gd 的 3D 版（掛在 AnimatedSprite3D 上，內容相同）。
## A3：待機動畫偶爾換成另一個動畫播一輪再換回來（例如感染者群站著那隻轉頭）。
## 換的時候接著目前的格數播，兩個動畫格數相同時（啃食＋轉頭），其他部分的動作不會中斷。
extends AnimatedSprite3D

@export var base_animation := &"eat"
@export var variant_animation := &"look"
## 每隔幾秒（在這個範圍內隨機）換一次，換過去播幾輪
@export var interval_min := 3.0
@export var interval_max := 6.0
@export var variant_loops := 1

var _wait := 0.0
var _loops_left := 0


func _ready() -> void:
	animation_looped.connect(_on_looped)
	play(base_animation)
	_wait = randf_range(interval_min, interval_max)


func _process(delta: float) -> void:
	if animation != base_animation or not is_playing():
		return
	_wait -= delta
	if _wait <= 0.0:
		_loops_left = variant_loops
		_switch(variant_animation)


func _on_looped() -> void:
	if animation != variant_animation:
		return
	_loops_left -= 1
	if _loops_left <= 0:
		_switch(base_animation)
		_wait = randf_range(interval_min, interval_max)


func _switch(anim: StringName) -> void:
	var f := frame
	var progress := frame_progress
	play(anim)
	set_frame_and_progress(f, progress)
