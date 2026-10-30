## B4-6：讓 3D 的像素人物用法線貼圖受光。掛在 AnimatedSprite3D（主角的 Sprite、人物的 Figure）底下的子節點：
## 換上 shaders/sprite_lit.gdshader 的材質，並依目前畫格用的是哪一張 spritesheet，給它整張圖和同名的「_normal.png」法線貼圖
## （主角的側面、正面／背面是兩張圖，換動畫時跟著換）。沒有法線貼圖的圖就當成平的。
## 法線貼圖用 art/tools/normal_map.py 由 spritesheet 產生，匯入設定要無損、不產生 mipmap。
extends Node

const SHADER := preload("res://shaders/sprite_lit.gdshader")

## 法線的強度（1＝照法線貼圖；越大越立體）
@export var normal_strength := 1.0

var _sprite: AnimatedSprite3D
var _mat: ShaderMaterial
var _atlas: Texture2D


func _ready() -> void:
	_sprite = get_parent() as AnimatedSprite3D
	if _sprite == null:
		return
	_mat = ShaderMaterial.new()
	_mat.shader = SHADER
	_mat.set_shader_parameter("normal_strength", normal_strength)
	_sprite.material_override = _mat
	_sprite.frame_changed.connect(_update)
	_sprite.animation_changed.connect(_update)
	_sprite.sprite_frames_changed.connect(_update)
	_update()


func _update() -> void:
	var frames := _sprite.sprite_frames
	if frames == null or not frames.has_animation(_sprite.animation):
		return
	var tex := frames.get_frame_texture(_sprite.animation, _sprite.frame)
	var atlas: Texture2D = tex.atlas if tex is AtlasTexture else tex
	if atlas == _atlas:
		return
	_atlas = atlas
	_mat.set_shader_parameter("albedo_tex", atlas)
	var normal_path := atlas.resource_path.get_basename() + "_normal.png"
	_mat.set_shader_parameter("normal_tex", load(normal_path) if ResourceLoader.exists(normal_path) else null)
