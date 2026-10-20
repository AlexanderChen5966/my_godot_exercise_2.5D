## B0-1 技術驗證：3D 版主角。沿 X 左右走、Z 前後走（縱深帶），不受重力，y 固定在地面。
## 1 公尺 ＝ 主角貼圖的 32 像素（主角 48px 高 ＝ 1.5 公尺）；2D 版畫面上 1 公尺 ＝ 64 螢幕像素（放大 2 倍）。
extends CharacterBody3D

const SPEED := 140.0 / 64.0  # 和 2D 版畫面上的速度一樣（140 螢幕像素／秒）
const DEPTH_SPEED_RATIO := 0.6  # 前後走得比左右慢，沿用 2D 版

var min_x := 0.5
var max_x := 35.5
var min_z := -1.5  # 縱深帶（腳的 z 範圍），由 b0_test.gd 依做法設定
var max_z := 1.5
var facing := 1  # 1 = 右，-1 = 左

@onready var sprite: AnimatedSprite3D = $Sprite


func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var old_position := position
	velocity = Vector3(direction.x * SPEED, 0.0, direction.y * SPEED * DEPTH_SPEED_RATIO)
	move_and_slide()
	position = Vector3(clampf(position.x, min_x, max_x), 0.0, clampf(position.z, min_z, max_z))
	if direction.x != 0.0:
		facing = 1 if direction.x > 0.0 else -1
	var moving := not position.is_equal_approx(old_position)
	var anim := ("walk_" if moving else "idle_") + ("right" if facing > 0 else "left")
	if sprite.animation != anim:
		sprite.play(anim)
