// B4-6：3D 的像素人物用法線貼圖受光（掛法見 scripts/sprite_lit_3d.gd）。
// AnimatedSprite3D 用 material_override 時，UV 仍是畫格在整張圖裡的位置，所以 albedo_tex／normal_tex 給整張 spritesheet。
// flip_h 會把 UV 左右顛倒：這時法線的 x 也要反過來，不然光會從另一邊照過來（B4-6 實驗看到的）。
// 淡出（modulate 的 alpha，例如女兒離開）用像素點陣（以像素圖的一格為單位）慢慢消失：維持不透明的畫法，才有影子、也不會和霧排序出錯。
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D albedo_tex : source_color, filter_nearest;
uniform sampler2D normal_tex : hint_normal, filter_nearest;
uniform float normal_strength = 1.0;

float bayer4(vec2 p) {
	int x = int(mod(p.x, 4.0));
	int y = int(mod(p.y, 4.0));
	int i = x + y * 4;
	int m[16] = int[](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(m[i]) + 0.5) / 16.0;
}

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	vec2 texel = floor(UV * vec2(textureSize(albedo_tex, 0)));   // 點陣對齊像素圖的格子（用螢幕座標會變成細網點）
	if (c.a < 0.5 || COLOR.a < bayer4(texel)) {
		discard;
	}
	ALBEDO = c.rgb * COLOR.rgb;
	vec3 n = texture(normal_tex, UV).rgb;
	if (dFdx(UV.x) < 0.0) {
		n.x = 1.0 - n.x;          // 畫格被左右翻轉
	}
	NORMAL_MAP = n;
	NORMAL_MAP_DEPTH = normal_strength;
}
