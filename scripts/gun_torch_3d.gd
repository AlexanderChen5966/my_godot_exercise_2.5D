## B1：gun_torch.gd 的 3D 版。裝在槍上的手電筒（警衛）：跟著人物動畫的格數，把聚光燈移到燈頭、沿著槍管往下照。
## 掛在 SpotLight3D，和人物的 Figure（AnimatedSprite3D）放在同一個父節點底下。每格燈頭的資料和 2D 版相同（art/design/a3/guard.py 印出）。
extends SpotLight3D

@export var follow: NodePath  # 人物的 AnimatedSprite3D（Figure）
## idle 每一格的（燈頭 x, 燈頭 y, 槍口往下的角度）：位置是圖上的像素（左上角為 0,0），人物面向左
@export var idle_frames := PackedVector3Array()
## event（瞄準）那一格的（燈頭 x, 燈頭 y, 角度）
@export var event_frame := Vector3.ZERO
## 光照到的地面有多遠（像素）：警衛巡視（guard_patrol.gd）的判定範圍。2D 版由錐形光貼圖的寬 × texture_scale × 0.65 算出
@export var floor_reach_px := 266.0

var _sprite: AnimatedSprite3D


func _ready() -> void:
	_sprite = get_node_or_null(follow) as AnimatedSprite3D
	_update()


func _process(_delta: float) -> void:
	_update()


func _update() -> void:
	if _sprite == null:
		return
	visible = _sprite.visible
	var f := event_frame
	if _sprite.animation != &"event" and not idle_frames.is_empty():
		f = idle_frames[_sprite.frame % idle_frames.size()]
	var frame_size := _sprite.sprite_frames.get_frame_texture(_sprite.animation, _sprite.frame).get_size()
	var local := (Vector2(f.x, f.y) - frame_size / 2.0) * _sprite.pixel_size
	var side := 1.0 if _sprite.flip_h else -1.0  # 面向右是 +1（圖是面向左畫的）
	var rad := deg_to_rad(f.z)
	position = _sprite.position + Vector3(-local.x if _sprite.flip_h else local.x, -local.y, 0.0)
	basis = Basis.looking_at(Vector3(side * cos(rad), -sin(rad), 0.0))  # 聚光燈往自己的 −Z 照
