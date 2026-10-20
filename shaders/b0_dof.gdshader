// B0-2 景深（網頁版 Compatibility 沒有內建景深，用 shader 模擬）：
// 掛在鏡頭前的全螢幕平面（Camera/Dof），讀畫面與深度，依和鏡頭的距離模糊。
// 焦點（focus_distance）由 b0_test.gd 每個畫面設成主角的距離；焦點前後 focus_range 公尺內清楚，
// 往後 far_ramp、往前 near_ramp 公尺內逐漸模糊到最大（max_radius 像素）。
// 每個取樣點只有在「它的模糊範圍蓋得到這裡」時才算進來；比較遠的取樣點用兩者中比較小的模糊程度，
// 所以模糊的背景不會蓋過清楚的主角，模糊的前景柱子則可以蓋過主角。
shader_type spatial;
render_mode unshaded, depth_draw_never, depth_test_disabled, cull_disabled, fog_disabled, shadows_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;
uniform bool enabled = true;
uniform float focus_distance = 14.3;
uniform float focus_range = 1.2;
uniform float far_ramp = 6.0;
uniform float near_ramp = 8.0;
uniform float max_radius = 8.0;  // 最大模糊半徑（像素，以 1152×768 為準）
uniform int taps = 24;           // 取樣數，越多越平滑、越吃效能

const float GOLDEN_ANGLE = 2.39996323;

float linear_distance(vec2 uv, mat4 inv_projection) {
	float depth = texture(depth_tex, uv).r;
	vec3 ndc = vec3(uv, depth) * 2.0 - 1.0;  // Compatibility（OpenGL）的深度是 0～1，換成 -1～1
	vec4 view = inv_projection * vec4(ndc, 1.0);
	return -view.z / view.w;
}

// 模糊程度 0～1
float coc(float dist) {
	float d = dist - focus_distance;
	if (d >= 0.0) {
		return clamp((d - focus_range) / far_ramp, 0.0, 1.0);
	}
	return clamp((-d - focus_range) / near_ramp, 0.0, 1.0);
}

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 1.0, 1.0);  // QuadMesh 1×1 → 蓋滿整個畫面
}

void fragment() {
	vec3 center = texture(screen_tex, SCREEN_UV).rgb;
	if (!enabled) {
		ALBEDO = center;
	} else {
		float center_dist = linear_distance(SCREEN_UV, INV_PROJECTION_MATRIX);
		float center_coc = coc(center_dist);
		vec2 px = 1.0 / VIEWPORT_SIZE * (VIEWPORT_SIZE.y / 768.0);
		vec3 sum = center;
		float weight = 1.0;
		for (int i = 1; i < taps; i++) {
			float r = sqrt(float(i) / float(taps)) * max_radius;
			float a = float(i) * GOLDEN_ANGLE;
			vec2 uv = SCREEN_UV + vec2(cos(a), sin(a)) * r * px;
			float sample_dist = linear_distance(uv, INV_PROJECTION_MATRIX);
			float sample_coc = coc(sample_dist);
			// 比較近的東西可以暈到後面（前景模糊蓋過主角）；比較遠的東西不能蓋過前面比較清楚的東西
			float reach = (sample_dist < center_dist ? sample_coc : min(sample_coc, center_coc)) * max_radius;
			float w = clamp(reach - r + 1.0, 0.0, 1.0);
			sum += texture(screen_tex, uv).rgb * w;
			weight += w;
		}
		ALBEDO = sum / weight;
	}
}
