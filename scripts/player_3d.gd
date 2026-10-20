## 3D 版主角（B1）：和 2D 版 player.gd 一樣的功能與介面，沿 X 左右走、Z 前後走（縱深帶），不受重力、y 固定在地面。
## 和 Main、區域資料之間的數值一律用 2D 的像素（64 像素＝1 公尺），自己的位置用公尺。can_move 為 false 時（對話中）不動。
## B0-3：除了左右，還有正面（往畫面外走）、背面（往畫面裡走）的走路與待機。
extends CharacterBody3D

const PX_PER_M := 64.0
const SPEED := 140.0 / PX_PER_M  # 和 2D 版畫面上的速度一樣（140 螢幕像素／秒），步履蹣跚
const DEPTH_SPEED_RATIO := 0.6  # 前後走得比左右慢，沿用 2D 版
# 角色在 32px 畫格裡偏左，左右兩套是互相翻轉的，所以兩個方向的位移不同，轉身時身體中心才不會跳動（2D 版的 3／-1 螢幕像素＝1.5／-0.5 貼圖像素）
const SPRITE_X_RIGHT := 1.5
const SPRITE_X_LEFT := -0.5
const SPRITE_Y := 24.0  # 畫格高 48，往上移一半，腳踩在原點
## A4：行走 6 格裡腳著地的兩格（第 0、3 格，正面／背面也一樣）；腳步聲在這兩格播放
const STEP_FRAMES := [0, 3]
const STEP_DB := -8.0
const STEP_STOP_FADE := 0.08  # A4-3：停下來時，正在播的腳步聲在這段時間內淡出

var can_move := false
var min_x := 0.25  # 公尺，由區域設定
var max_x := 35.75
var min_z := -1.5  # 縱深帶（腳的 z 範圍，公尺），由區域設定
var max_z := 1.5
var facing := 1  # 1 = 右，-1 = 左
## 面向哪一邊："right"／"left"＝側面，"front"＝面向鏡頭，"back"＝背對鏡頭
var view := "right"
var acting := false  # A3：正在做動作（調查時伸手），這段時間不切換待機／行走
var lean := false    # A3：衝動強度高，站著不動時改成前傾（由 Main 每個畫面設定）
var lean_toward := NAN  # 前傾時轉向的 x（像素，衝動最強的那個人）
var step_sounds: Array[AudioStream] = []  # A4：目前區域地面的腳步聲（由 Main 依區域資料的 floor 設定）
var steps_played := 0  # 播過幾次腳步聲（測試用）
var in_cover := false  # A5 躲藏：躲在掩護後面（變暗、半透明）；一移動就出來

var _steps: AudioStreamPlayer
var _steps_tween: Tween

@onready var sprite: AnimatedSprite3D = $Sprite


func _ready() -> void:
	_steps = AudioStreamPlayer.new()
	_steps.name = "Steps"
	_steps.bus = &"SFX"
	_steps.volume_db = STEP_DB
	_steps.max_polyphony = 2
	add_child(_steps)
	sprite.frame_changed.connect(_on_frame_changed)


func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down") if can_move else Vector2.ZERO
	if in_cover and direction != Vector2.ZERO:
		set_in_cover(false)  # 移動就從掩護後面出來
	var old_position := position
	velocity = Vector3(direction.x * SPEED, 0.0, direction.y * SPEED * DEPTH_SPEED_RATIO)
	move_and_slide()
	position = Vector3(clampf(position.x, min_x, max_x), 0.0, clampf(position.z, min_z, max_z))
	# 有左右方向（含斜著走）用側面；只有前後時用正面／背面。停下來保持最後的方向
	if direction.x != 0.0:
		facing = 1 if direction.x > 0.0 else -1
		view = "right" if facing > 0 else "left"
	elif direction.y != 0.0:
		view = "front" if direction.y > 0.0 else "back"
	_update_animation(not position.is_equal_approx(old_position))  # 走到邊緣被擋住時改回待機


## 主角的 x（像素）
func px_x() -> float:
	return position.x * PX_PER_M


## 直接設定面向（換區域時使用），並立刻換成對應的待機動畫。
func face(direction: int) -> void:
	_face_side(direction)
	_update_animation(false)


## A3：調查時轉向物件（x 像素）並伸手，停在最後一格，直到 end_action()
func reach_toward(x: float) -> void:
	if not is_nan(x) and absf(x - px_x()) > 4.0:
		_face_side(1 if x > px_x() else -1)
	elif view == "front" or view == "back":
		_face_side(facing)  # 伸手只有側面的動畫
	acting = true
	sprite.play("reach_right" if facing > 0 else "reach_left")
	_set_sprite_x()


func end_action() -> void:
	acting = false


## A5 躲藏：躲到掩護後面／出來（樣子先用變暗、半透明）
func set_in_cover(value: bool) -> void:
	in_cover = value
	sprite.modulate = Color(0.35, 0.35, 0.42, 0.6) if value else Color.WHITE
	# 半透明要關掉 alpha cut 才看得出來（alpha cut 只有「畫」或「不畫」）
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISABLED if value else SpriteBase3D.ALPHA_CUT_DISCARD


## A5：比出手勢「我——在——這——裡」（約 2 秒）。toward_x（像素）有值時先轉向那個人。播完才結束，用 await 等。
func play_gesture(toward_x := NAN) -> void:
	if not is_nan(toward_x) and absf(toward_x - px_x()) > 4.0:
		_face_side(1 if toward_x > px_x() else -1)
	elif view == "front" or view == "back":
		_face_side(facing)  # 手勢只有側面的動畫
	acting = true
	_fade_out_step()
	sprite.play("gesture_right" if facing > 0 else "gesture_left")
	_set_sprite_x()
	await sprite.animation_finished
	acting = false
	_update_animation(false)


func _face_side(direction: int) -> void:
	facing = direction
	view = "right" if facing > 0 else "left"


## 依「是否移動 × 面向」選擇動畫；站著時衝動強度高就前傾（前傾只有側面，所以會轉向那個人）
func _update_animation(moving: bool) -> void:
	if acting:
		return
	if lean and not moving and not is_nan(lean_toward) and absf(lean_toward - px_x()) > 4.0:
		_face_side(1 if lean_toward > px_x() else -1)  # 被人吸引：朝著那個人前傾
	var side := view == "right" or view == "left"
	var anim := ("walk_" if moving else ("lean_" if lean and side else "idle_")) + view
	if sprite.animation != anim:
		var was_walking := String(sprite.animation).begins_with("walk_")
		sprite.play(anim)
		if moving:
			_play_step()  # 開始走的第一格（第 0 格）就是腳著地，frame_changed 不會觸發
		elif was_walking:
			_fade_out_step()
	_set_sprite_x()


func _set_sprite_x() -> void:
	if view == "right":
		sprite.offset = Vector2(SPRITE_X_RIGHT, SPRITE_Y)
	elif view == "left":
		sprite.offset = Vector2(SPRITE_X_LEFT, SPRITE_Y)
	else:
		sprite.offset = Vector2(0.0, SPRITE_Y)


## A4：行走到腳著地的那兩格時播放腳步聲（地面材質由區域決定，每次隨機挑一個、音高稍微變化）
func _on_frame_changed() -> void:
	if String(sprite.animation).begins_with("walk_") and sprite.frame in STEP_FRAMES:
		_play_step()


func _play_step() -> void:
	if step_sounds.is_empty():
		return
	if _steps_tween:
		_steps_tween.kill()
	_steps.volume_db = STEP_DB
	_steps.stream = step_sounds[randi() % step_sounds.size()]
	_steps.pitch_scale = randf_range(0.92, 1.08)
	_steps.play()
	steps_played += 1


func _fade_out_step() -> void:
	if not _steps.playing:
		return
	if _steps_tween:
		_steps_tween.kill()
	_steps_tween = create_tween()
	_steps_tween.tween_property(_steps, "volume_db", -40.0, STEP_STOP_FADE)
	_steps_tween.tween_callback(_steps.stop)
