## B1：flicker_light.gd 的 3D 版（掛在 OmniLight3D／SpotLight3D 上，內容相同，亮度寫到 light_energy）。
## 警示燈閃爍：緩慢的呼吸式明暗，偶爾突然熄滅一下（接觸不良的感覺）。
extends Light3D

@export var base_energy := 5.0
@export var pulse_speed := 1.6         # 呼吸的速度（每秒弧度倍率）
@export_range(0.0, 1.0, 0.05) var min_ratio := 0.35  # 最暗時是 base_energy 的幾倍
@export_range(0.0, 1.0, 0.001) var dropout_chance := 0.012  # 每個畫面突然熄滅的機率
@export_range(0.0, 1.0, 0.05) var dropout_ratio := 0.05  # 熄滅時剩 base_energy 的幾倍（太低時整個畫面會跟著閃）
## A3：跟著火焰動畫（AnimatedSprite3D）一起跳動：每一格乘上 frame_strength 的倍率（火焰高的格亮一點）。不設定時照舊。
## 用 NodePath（不用節點型別的 export）：Toolkit 設定節點型別的 export 時只寫入路徑，載入後會是 null
@export var follow: NodePath
@export var frame_strength := PackedFloat32Array()
## A3：燈突然熄滅時，把這個 Sprite3D（hframes 2：0 亮、1 熄）切到熄滅那格，例如停車場的燈管
@export var off_sprite: NodePath
## A4：燈的嗡聲（AudioStreamPlayer3D）熄滅時靜音；熄滅的瞬間播放 dropout_sound（例如燈管啟動器的喀喀聲，最少間隔 sound_cooldown 秒）
@export var hum: NodePath
@export var dropout_sound: NodePath
@export var sound_cooldown := 4.0

var _time := 0.0
var _dropout_left := 0.0
var _follow: AnimatedSprite3D
var _off_sprite: Sprite3D
var _hum: AudioStreamPlayer3D
var _dropout_sound: AudioStreamPlayer3D
var _hum_db := 0.0
var _since_sound := 99.0


func _ready() -> void:
	if not follow.is_empty():
		_follow = get_node_or_null(follow) as AnimatedSprite3D
	if not off_sprite.is_empty():
		_off_sprite = get_node_or_null(off_sprite) as Sprite3D
	if not hum.is_empty():
		_hum = get_node_or_null(hum) as AudioStreamPlayer3D
		if _hum:
			_hum_db = _hum.volume_db
	if not dropout_sound.is_empty():
		_dropout_sound = get_node_or_null(dropout_sound) as AudioStreamPlayer3D


func _process(delta: float) -> void:
	_time += delta
	_since_sound += delta
	if _hum:
		_hum.volume_db = -80.0 if _dropout_left > 0.0 else _hum_db
	if _off_sprite:
		_off_sprite.frame = 1 if _dropout_left > 0.0 else 0
	if _dropout_left > 0.0:
		_dropout_left -= delta
		light_energy = base_energy * dropout_ratio
		return
	if randf() < dropout_chance:
		_dropout_left = randf_range(0.05, 0.15)
		if _dropout_sound and _since_sound >= sound_cooldown:
			_dropout_sound.play()
			_since_sound = 0.0
	var pulse := sin(_time * pulse_speed) * 0.5 + 0.5
	light_energy = base_energy * lerpf(min_ratio, 1.0, pulse) * _frame_factor()


func _frame_factor() -> float:
	if _follow == null or frame_strength.is_empty():
		return 1.0
	return frame_strength[_follow.frame % frame_strength.size()]
