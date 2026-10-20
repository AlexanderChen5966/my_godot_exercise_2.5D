## 衝動機制（甲）的畫面與聲音：紅色暈影、心跳、手電筒閃爍。掛在 Main 的 ImpulseOverlay（全螢幕 ColorRect）上。
## Main 每個畫面設定 target（0～1，依主角與人的距離、事件是否進行中），這裡平滑地跟上並產生效果。
## 強度都在下面的 @export，可以在編輯器的屬性面板直接調整。
extends ColorRect

signal beat  # A5：每次心跳（壓抑衝動時，量表被拉掉一點）

@export_group("範圍")
## 互動點的 impulse 沒寫 range 時，從多遠開始有感覺（px）
@export var default_range := 420.0
## 進入這個距離（px）就算最強（互動點觸發範圍的一半寬）
@export var full_distance := 80.0
## 強度跟上目標的速度（每秒）：越大反應越快；淡出用 fade_out_speed
@export var fade_in_speed := 1.2
@export var fade_out_speed := 0.8

@export_group("紅色暈影")
@export_range(0.0, 1.0, 0.01) var max_red := 0.75
@export var red_tint := Color(0.75, 0.02, 0.05)

@export_group("心跳")
## 心跳間隔（秒）：剛有感覺時慢，最強時快
@export var beat_interval_far := 1.1
@export var beat_interval_near := 0.42
## 音量（dB）：剛有感覺時小聲，最強時大聲
@export var beat_db_far := -26.0
@export var beat_db_near := -2.0
## A4：心跳的錄音本身就是一組兩拍（撲通）時打開，程式不再補第二聲
@export var sample_has_two_beats := true
## 一次心跳兩聲（撲通）：第二聲延遲幾秒、小聲多少 dB（sample_has_two_beats 關閉時才用）
@export var second_beat_delay := 0.16
@export var second_beat_db := -5.0

@export_group("手電筒")
## 最強時每秒閃爍幾次、每次暗到原本的幾倍
@export var flicker_per_second := 5.0
@export_range(0.0, 1.0, 0.05) var flicker_dim := 0.25

var target := 0.0     # Main 設定的目標強度
var intensity := 0.0  # 目前的強度（平滑後）

var _light: Node  # 2D 的 PointLight2D 或 3D 的 Light3D
var _energy_property := &"energy"
var _light_energy := 1.0
var _beat_wait := 0.0
var _second_beat_at := -1.0
var _pulse := 0.0
var _flicker_left := 0.0

@onready var heartbeat: AudioStreamPlayer = $Heartbeat


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	(material as ShaderMaterial).set_shader_parameter("tint", red_tint)


## 換區域時指定要閃爍的手電筒與它原本的亮度（沒有區域時傳 null）
## B1：2D 是 PointLight2D（energy），3D 是 Light3D（light_energy）
func set_flashlight(light: Node, base_energy: float) -> void:
	_light = light
	_light_energy = base_energy
	_energy_property = &"light_energy" if light is Light3D else &"energy"


## 立即歸零（回標題、換場時）
func reset() -> void:
	target = 0.0
	intensity = 0.0
	_pulse = 0.0
	_second_beat_at = -1.0
	_apply()


## 距離 → 目標強度：range 外是 0，full_distance 內是 1，中間線性變化
func strength_at(distance: float, range_px: float) -> float:
	if range_px <= full_distance:
		return 1.0 if distance <= full_distance else 0.0
	return clampf(1.0 - (distance - full_distance) / (range_px - full_distance), 0.0, 1.0)


func _process(delta: float) -> void:
	var speed := fade_in_speed if target > intensity else fade_out_speed
	intensity = move_toward(intensity, target, speed * delta)
	_pulse = move_toward(_pulse, 0.0, delta * 4.0)
	_update_heartbeat(delta)
	_update_flicker(delta)
	_apply()


func _update_heartbeat(delta: float) -> void:
	if _second_beat_at >= 0.0:
		_second_beat_at -= delta
		if _second_beat_at < 0.0:
			_play_beat(second_beat_db)
	if intensity <= 0.02:
		_beat_wait = 0.0
		return
	_beat_wait -= delta
	if _beat_wait <= 0.0:
		_play_beat(0.0)
		beat.emit()
		if not sample_has_two_beats:
			_second_beat_at = second_beat_delay
		_beat_wait = lerpf(beat_interval_far, beat_interval_near, intensity)
		_pulse = 1.0


func _play_beat(extra_db: float) -> void:
	heartbeat.volume_db = lerpf(beat_db_far, beat_db_near, intensity) + extra_db
	heartbeat.play()


func _update_flicker(delta: float) -> void:
	if not is_instance_valid(_light):
		return
	if _flicker_left > 0.0:
		_flicker_left -= delta
		_light.set(_energy_property, _light_energy * flicker_dim)
		return
	if intensity > 0.05 and randf() < flicker_per_second * intensity * intensity * delta:
		_flicker_left = randf_range(0.04, 0.12)
	_light.set(_energy_property, _light_energy)


func _apply() -> void:
	var mat := material as ShaderMaterial
	mat.set_shader_parameter("intensity", intensity)
	mat.set_shader_parameter("max_alpha", max_red)
	mat.set_shader_parameter("pulse", _pulse)
	visible = intensity > 0.001
