// B0-2 3D 霧：A2 的霧（shaders/fog.gdshader）改成 3D 版，貼在主角後面的一片半透明平面上（ParkingLot3D/Fog）。
// 會受 3D 燈光影響：暗處幾乎看不見，被燈照到的地方才浮現。rect_size 是平面大小換成貼圖像素（1 公尺 ＝ 32 像素），
// pixel_size 讓霧也有像素感。
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform vec4 fog_color : source_color = vec4(0.75, 0.75, 0.8, 1.0);
uniform float density : hint_range(0.0, 1.0) = 0.3;
uniform vec2 speed = vec2(0.006, 0.0015);
uniform vec2 noise_scale = vec2(2.0, 1.0);
uniform float top_fade : hint_range(0.0, 1.0) = 0.45;
uniform float bottom_fade : hint_range(0.0, 1.0) = 0.15;
uniform vec2 rect_size = vec2(1280.0, 160.0);
uniform float pixel_size = 2.0;

void fragment() {
	vec2 uv = floor(UV * rect_size / pixel_size) * pixel_size / rect_size;
	float n1 = texture(noise_tex, uv * noise_scale + TIME * speed).r;
	float n2 = texture(noise_tex, uv * noise_scale * 1.7 + vec2(0.37, 0.61) - TIME * speed * 1.3).r;
	float n = smoothstep(0.25, 0.9, n1 * 0.6 + n2 * 0.4);
	float edge = smoothstep(0.0, top_fade, uv.y) * (1.0 - smoothstep(1.0 - bottom_fade, 1.0, uv.y));
	// 透明度分成幾階，避免平滑漸層破壞像素風
	ALBEDO = fog_color.rgb;
	ALPHA = floor(n * edge * density * 24.0) / 24.0;
}
