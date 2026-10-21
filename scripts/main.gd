## 主畫面：顯示場景與選項；點選項後先顯示 response，再點擊前往 next_id。
## 主文字與 response 以打字機效果顯示，換場時背景淡出淡入，BGM 以兩個播放器交替淡入淡出。
extends Control

enum State { TITLE, TRANSITION, TYPING, CHOOSING, RESPONSE, EXPLORE, AREA_TEXT, GESTURE, FLASHBACK, RESIST }  # GESTURE：A5 比手勢中（不能移動、不接受其他按鍵）；FLASHBACK：A5 記憶閃回中（按互動鍵跳過）；RESIST：A5 壓抑衝動（按住或連打，見 RESIST_HOLD）

const EXTRA_HINT_COLOR := "#a8a8a8"
const CHOSEN_MODULATE := Color(1, 1, 1, 0.45)
const CHARS_PER_SECOND := 30.0
const SILENT_CHARS := " \n，。、！？：；「」『』（）…—,.!?:;\"'()-"  # 打到這些字元時不出打字聲
const FADE_HALF_TIME := 0.2  # 淡出 + 淡入共約 0.4 秒
const BGM_FADE_TIME := 0.8
const AMB_FADE_TIME := 1.2  # A4：環境音換區域時的交叉淡化
const POOL_SIZE := 4  # A4：音效、介面音各準備幾個播放器輪流用
## A4-3：有聲音的轉場（出口的開門聲、Bad End 的槍聲）在黑畫面多停幾秒，讓聲音在黑幕中播完再進下一個畫面（作者：聲音在轉場後才出來很怪）
const SOUND_HOLD_TIME := 0.7
## A6：標題選單與設定面板的顏色（選中＝金色）
const MENU_COLOR := Color(0.78, 0.78, 0.78)
const MENU_FOCUS_COLOR := Color(0.91, 0.81, 0.54)
const CREDITS_FILE := "res://data/credits.json"
const CREDITS_SCROLL_STEP := 60  # ↑↓ 一次捲動幾 px
## A5 手勢：互動點的 gesture 沒寫 range 時，多遠內有反應（px）；比手勢時的布料聲（Kenney cloth3）；第一次可以走動時的按鍵提示
const GESTURE_RANGE := 360.0
const GESTURE_SFX := "inspect_4.ogg"
const GESTURE_HINT := "G　比出手勢"
const GESTURE_HINT_TIME := 4.0
## A5 記憶閃回：白光亮起、白光退去（露出插畫）、停留、淡出淡入回到區域的秒數（docs/A5_記憶閃回設計.md）
const FLASHBACK_FLASH := 0.12
const FLASHBACK_REVEAL := 0.2
const FLASHBACK_TIME := 2.2
const FLASHBACK_FADE := 0.3
## A5 壓抑衝動：量表每秒自己掉多少、每次心跳被拉掉多少、沒寫 time 時的時限；判定後鎖住按鍵多久
## （連打的空白鍵不能直接按到剛出現的選項，也不能跳過撲上去的回應文字）
const RESIST_DRAIN := 0.12
const RESIST_TUG := 0.05
const RESIST_TIME := 5.0
const RESIST_LOCK_MS := 900
## 抵抗的操作（作者 2026-10-16）：true＝按住空白鍵（測試版，量表依資料的 hold 秒數上漲）；false＝連打（正式版，依 presses 次數）。正式版改回 false。
const RESIST_HOLD := true
const RESIST_HOLD_TIME := 2.0  # 資料沒寫 hold 時要按住幾秒
## A5 躲藏：警衛的巡視（轉身、光錐判定）；被發現時的聲音（Kenney 金屬喀嚓，像槍上膛）；躲起來時的布料聲
const GuardPatrol := preload("res://scripts/guard_patrol.gd")
const SPOTTED_SFX := "pickup_2.ogg"
const HIDE_SFX := "inspect_4.ogg"
## A4：互動點沒有寫 sfx 時，依類型播放的聲音（出口在通過時才播自己的 sfx）
const TYPE_SFX := { "inspect": "inspect", "item": "pickup" }
const LOCKED_TEXT := "……（你想不起來）"   # 數值不夠時，選項顯示的文字
const ENDING_LABEL := "— 結局 —"
const BAD_ENDING_COLOR := Color(0.85, 0.35, 0.3)
const CHOICE_GUARD_MS := 300  # 選項出現後這段時間內不接受選擇：避免想跳過打字時剛好選到第一個選項
const BASE_SIZE := Vector2(1152, 768)
const PROMPT_GAP := 8.0  # 提示和頭頂的距離
const LEAN_FROM := 0.5   # A3：衝動強度到這裡，主角站著時改成前傾

# 節點都設為 unique name（%Name），之後搬動節點層級時不用改這裡。
@onready var background: TextureRect = %Background
@onready var world: Node2D = %World
@onready var fade: ColorRect = %Fade
@onready var title_layer: Control = %TitleLayer
@onready var title_label: Label = %TitleLabel
@onready var start_label: Label = %StartLabel  # A6 起不用（改成選單），保留節點
@onready var title_menu: VBoxContainer = %TitleMenu  # A6：開始遊戲／設定／製作群
@onready var start_button: Button = %StartButton
@onready var settings_button: Button = %SettingsButton
@onready var credits_button: Button = %CreditsButton
@onready var settings_panel: PanelContainer = %SettingsPanel  # A6：音量與打字聲（scripts/game_settings.gd）
@onready var music_slider: HSlider = %MusicSlider
@onready var sfx_slider: HSlider = %SfxSlider
@onready var ambient_slider: HSlider = %AmbientSlider
@onready var typing_toggle: Button = %TypingToggle
@onready var back_button: Button = %BackButton
@onready var credits_panel: PanelContainer = %CreditsPanel  # A6：製作群（內容在 data/credits.json，Godot 授權由引擎提供）
@onready var credits_scroll: ScrollContainer = %CreditsScroll
@onready var credits_text: RichTextLabel = %CreditsText
@onready var credits_back: Button = %CreditsBack
@onready var story_layer: Control = %StoryLayer
@onready var dialog_panel: PanelContainer = %DialogPanel
@onready var ending_tag: Label = %EndingTag
@onready var scene_title: Label = %SceneTitle
@onready var body: RichTextLabel = %Body
@onready var hint: RichTextLabel = %Hint
@onready var continue_label: Label = %Continue
@onready var choices_box: VBoxContainer = %Choices
@onready var bgm_players: Array[AudioStreamPlayer] = [%BgmA, %BgmB]
@onready var sfx: AudioStreamPlayer = %Sfx
@onready var type_sfx: AudioStreamPlayer = %TypeSfx
@onready var amb_players: Array[AudioStreamPlayer] = [%AmbA, %AmbB]  # A4：區域環境音，兩個交替淡入淡出
@onready var event_sfx: AudioStreamPlayer = %EventSfx  # A4：互動、事件音（和下面幾個複製出來的播放器輪流用，可以重疊）
@onready var ui_sfx: AudioStreamPlayer = %UiSfx        # A4：選項游標、確認
@onready var rotate_hint: ColorRect = %RotateHint
@onready var prompt_label: Label = %PromptLabel
@onready var flashback: TextureRect = %Flashback  # A5 記憶閃回的插畫（shaders/flashback.gdshader：褪色、雜訊、暗角）
@onready var flash: ColorRect = %Flash             # 閃回開始時的白光
@onready var resist_box: VBoxContainer = %Resist  # A5 壓抑衝動的提示與量表（在對話框裡）
@onready var resist_label: Label = %ResistLabel
@onready var resist_bar: ProgressBar = %ResistBar
@onready var impulse_fx: ColorRect = %ImpulseOverlay  # 衝動機制的紅色暈影、心跳、手電筒閃爍（scripts/impulse_fx.gd）
@onready var camera_fx: Node = %CameraFx  # A2-4 鏡頭的推近、震動、晃動（scripts/camera_fx.gd）

var story := StoryData.new()
var areas := AreaData.new()
## B1：區域用 3D 版（scenes/areas3d/<名稱>3D.tscn），還沒做 3D 版的區域照舊用 2D。
## 預設值在專案設定 game/areas_3d；遊玩測試在載入 Main 之前設定（2D／3D 兩種都要能跑）。
var use_3d_areas: bool = ProjectSettings.get_setting("game/areas_3d", false)
var _area: Node = null  # 目前在 World 底下的區域場景（2D 的 area.gd 或 3D 的 area_3d.gd，介面相同）
var _area_id := ""
var _nearby_point := ""      # 玩家目前所在範圍內、可按互動鍵的互動點
var _closing_point := ""     # 目前顯示的區域文字屬於哪個互動點（開場文字為空字串）
var _closing_view: Dictionary = {}  # 打開時套用 variants 後的互動點內容（關閉時用同一份，不受途中狀態改變影響）
var _area_choosing := false  # 目前的選項屬於區域的 choice 互動點（不是視覺小說的選項）
var _area_choice: Dictionary = {}     # 區域裡選了哪個選項（有 to 時，關閉文字後前往）
var _pending_choice: Dictionary = {}  # 視覺小說裡選了哪個選項（回應讀完後決定去處）
var _checkpoint: Dictionary = {}      # Bad End「從這裡重試」回到的位置與狀態
var _choices_shown_at := 0           # 選項出現的時間（毫秒，給 CHOICE_GUARD_MS 用）
var _impulse_released := false        # 有 impulse 的事件已經選完（張力開始淡出）
var _impulse_x := NAN                 # A3：衝動最強的那個人的 x（主角前傾時轉向他）
var _debug_label: Label               # F3 數值顯示（只在 debug 版建立）
var current_id: int = -1
var state: State = State.TITLE
var _pending_next_id: int = -1
var _chosen_in_scene: Dictionary = {}  # 本場景已選過的選項索引（留在原地時變暗）

var _button_styles: Dictionary = {}  # 狀態名稱 -> StyleBoxFlat
var _typing_tween: Tween
var _after_typing: Callable
var _typed_text := ""        # 目前打字中的純文字（判斷標點用）
var _typed_count := 0
var _next_tick_at := 0        # 打到第幾個字時發出下一次打字聲
var _type_base_db := 0.0

var _audio_unlocked := false  # 瀏覽器要求使用者互動後才能播放聲音
var _bgm_file := ""           # 目前播放（或淡入中）的曲目
var _bgm_index := 0           # bgm_players 中目前使用的播放器
var _bgm_tween: Tween
var _amb_file := ""
var _amb_index := 0
var _amb_tween: Tween
var _quiet_focus := false     # 自動聚焦第一個選項時不出游標聲
var _hold_black := 0.0        # 下一次轉場在黑畫面多停幾秒（出口播了開門聲時）
var _gesture_hint: Label      # A5：「G　比出手勢」（第一次可以走動時顯示一次）
var _gesture_hint_shown := false
var _flashback_tween: Tween
var _flashback_ending := false
var _resist: Dictionary = {}     # 目前事件的 resist 設定（hold／presses、time、fail）
var resist_value := 0.0          # 量表 0～1
var _resist_left := 0.0          # 剩幾秒
var _input_locked_until := 0     # 這個時間（毫秒）之前不接受按鍵
var patrols: Dictionary = {}     # A5 躲藏：互動點編號 → 警衛巡視節點（guard_patrol.gd）

signal flashback_finished  # A5：閃回播完（或被跳過）、回到區域
var _pools := {}  # 播放器 → 輪流用的播放器陣列
var sound_log: Array[String] = []  # 最近播過的音效名稱（測試與 MCP 驗證用，最多 20 個）
var _sliders := {}  # A6：設定鍵 → 音量條


func _ready() -> void:
	_type_base_db = type_sfx.volume_db
	GameSettings.load_settings()  # A6：音量、打字聲
	SoundLib.register_all()  # 網頁版：先把音效交給瀏覽器解碼，第一次播放時才不會延遲
	# A4：每種聲音準備幾個播放器輪流用，讓聲音可以重疊（低吼＋確認音）。
	# 不用 AudioStreamPolyphonic：網頁版預設的 Sample 播放模式不一定支援，一般的播放器最保險。
	for player in [event_sfx, ui_sfx]:
		var pool: Array[AudioStreamPlayer] = [player]
		for i in POOL_SIZE - 1:
			var copy := player.duplicate() as AudioStreamPlayer
			copy.name = "%s%d" % [player.name, i + 2]
			copy.unique_name_in_owner = false
			add_child(copy)
			pool.append(copy)
		_pools[player] = pool
	camera_fx.set_background(background)
	_setup_style()
	_setup_title_menu()
	get_window().size_changed.connect(_on_window_resized)
	_on_window_resized()
	if not story.load_story():
		return
	areas.load_areas()
	if OS.is_debug_build():
		_create_debug_label()
	_create_gesture_hint()
	impulse_fx.beat.connect(_on_heartbeat)
	show_title()


## StyleBox 與主題覆寫在這裡設定（按鈕是動態產生的，樣式需由程式套用）。
func _setup_style() -> void:
	# A5 壓抑衝動的量表：深色底、淡米色的量
	var bar_bg := StyleBoxFlat.new()
	bar_bg.bg_color = Color(1, 1, 1, 0.15)
	bar_bg.set_corner_radius_all(6)
	var bar_fill := StyleBoxFlat.new()
	bar_fill.bg_color = Color(0.78, 0.75, 0.69)
	bar_fill.set_corner_radius_all(6)
	resist_bar.add_theme_stylebox_override("background", bar_bg)
	resist_bar.add_theme_stylebox_override("fill", bar_fill)
	var box := StyleBoxFlat.new()
	box.bg_color = Color(0, 0, 0, 0.65)
	box.set_corner_radius_all(8)
	box.set_content_margin_all(20)
	dialog_panel.add_theme_stylebox_override("panel", box)

	scene_title.add_theme_font_size_override("font_size", 26)
	scene_title.add_theme_color_override("font_color", Color(1.0, 0.86, 0.6))
	body.add_theme_font_size_override("normal_font_size", 20)
	body.add_theme_constant_override("line_separation", 6)
	hint.add_theme_font_size_override("normal_font_size", 18)
	continue_label.add_theme_font_size_override("font_size", 18)
	continue_label.add_theme_color_override("font_color", Color(1.0, 0.86, 0.6))

	choices_box.add_theme_constant_override("separation", 10)
	var bg_colors := {
		"normal": Color(0.08, 0.08, 0.1, 0.8),
		"hover": Color(0.25, 0.2, 0.12, 0.9),
		"pressed": Color(0.4, 0.3, 0.15, 0.95),
	}
	for style_name in bg_colors:
		var sb := StyleBoxFlat.new()
		sb.bg_color = bg_colors[style_name]
		sb.set_corner_radius_all(6)
		sb.set_border_width_all(1)
		sb.border_color = Color(1.0, 0.86, 0.6, 0.5)
		sb.content_margin_left = 16
		sb.content_margin_right = 16
		sb.content_margin_top = 10
		sb.content_margin_bottom = 10
		_button_styles[style_name] = sb
	_button_styles["focus"] = _button_styles["hover"]
	var disabled: StyleBoxFlat = _button_styles["normal"].duplicate()
	disabled.bg_color = Color(0.05, 0.05, 0.06, 0.55)
	disabled.border_color = Color(1.0, 0.86, 0.6, 0.15)
	_button_styles["disabled"] = disabled


func show_title() -> void:
	current_id = -1
	_free_area()  # 從區域中回到標題時，一併釋放區域
	background.visible = true
	dialog_panel.visible = true
	title_label.text = story.game_title
	background.texture = load(StoryData.bg_path(story.title_screen["bg"]))
	title_layer.visible = true
	story_layer.visible = false
	ending_tag.visible = false
	if fade.color.a > 0.0:
		# 從結局回來：黑幕淡出後才接受點擊
		state = State.TRANSITION
		var tween := create_tween()
		tween.tween_property(fade, "color:a", 0.0, FADE_HALF_TIME)
		tween.tween_callback(func() -> void: state = State.TITLE)
	else:
		state = State.TITLE
	play_ambience("")
	if _audio_unlocked:
		play_bgm(story.title_screen["bgm"])
	start_label.visible = false
	settings_panel.visible = false
	credits_panel.visible = false
	title_menu.visible = true
	title_label.visible = true
	_quiet_focus = true
	start_button.grab_focus()
	_quiet_focus = false


func _start_game() -> void:
	GameState.reset(story.stats)  # 新的一輪：清空旗標、物品，數值回到初始值
	_audio_unlocked = true
	get_viewport().gui_release_focus()  # 選單的焦點拿掉，避免之後的按鍵又按到選單
	state = State.TRANSITION
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 1.0, FADE_HALF_TIME)
	tween.tween_callback(func() -> void:
		title_layer.visible = false
		story_layer.visible = true
		scene_title.text = ""
		body.text = ""
		_clear_choices()
		hint.visible = false
		continue_label.visible = false
		_checkpoint = {}
		if not story.start_area.is_empty():
			enter_area(story.start_area, -1, false)  # v1.5：直接從停車場開始
		else:
			show_scene(story.start_id, false)
	)


## 區域資料的 scene（2D 場景）→ 實際要載入的場景：開 3D 時，有同名的 3D 版就用 3D 版
## 例如 res://scenes/areas/ParkingLot.tscn → res://scenes/areas3d/ParkingLot3D.tscn
func area_scene_path(area: Dictionary) -> String:
	var path := str(area["scene"])
	if use_3d_areas:
		var path_3d := AreaData.scene_path_3d(path)
		if ResourceLoader.exists(path_3d):
			return path_3d
	return path


## 把區域場景實例化到 World 底下（同時只會有一個區域）。
## from_area：從哪個區域走過來，用來決定出現位置（spawns）；從視覺小說進來時為空字串。
func _instantiate_area(area_id: String, from_area := "") -> Node:
	_free_area()
	var area := areas.get_area(area_id)
	_area = (load(area_scene_path(area)) as PackedScene).instantiate()
	_area_id = area_id
	_nearby_point = ""
	world.add_child(_area)
	_area.player.step_sounds = SoundLib.variants("step_" + str(area.get("floor", "concrete")))  # A4：地面材質決定腳步聲
	impulse_fx.set_flashlight(_area.get_node_or_null("Player/Flashlight"), _area.flashlight_energy)
	camera_fx.set_camera(_area.camera, _area)
	_area.point_entered.connect(_on_point_entered)
	_area.point_exited.connect(_on_point_exited)
	var spawns: Dictionary = area.get("spawns", {})
	var spawn_key := from_area if spawns.has(from_area) else "default"
	if spawns.has(spawn_key):
		var spawn = spawns[spawn_key]  # x，或 [x, y]（A1.5）
		if spawn is Array:
			_area.place_player(float(spawn[0]), float(spawn[1]))
		else:
			_area.place_player(float(spawn))
	# 已經完成的事件（例如婦人逃走），回到這個區域時不再出現
	var points: Dictionary = area.get("points", {})
	for point_id in points:
		if _is_done(point_id) and _hides_when_done(points[point_id]):
			_area.consume_point(point_id)
	_setup_patrols()
	return _area


func _free_area() -> void:
	patrols.clear()
	if _area:
		_area.queue_free()
		_area = null
	impulse_fx.set_flashlight(null, 1.0)
	impulse_fx.reset()
	camera_fx.set_camera(null)
	_area_id = ""
	_nearby_point = ""
	_area_choosing = false
	prompt_label.visible = false


## 進入區域：淡出 → 實例化區域到 World → 隱藏 Background → 換 BGM → 淡入 → 開場文字（同一輪只顯示一次）。
## fade_out 為 false 時表示畫面已經是黑的（例如從標題「開始」進來）。
## from_area：從另一個區域走過來時的來源區域（決定出現位置）。
func enter_area(area_id: String, scene_id: int, fade_out := true, from_area := "") -> void:
	var area := areas.get_area(area_id)
	_save_checkpoint({ "area": area_id, "from": from_area })  # 進入區域時的狀態（開場還沒看過）
	current_id = scene_id
	state = State.TRANSITION
	if area.has("bgm"):
		play_bgm(area["bgm"])
	play_ambience(area.get("ambience", ""))
	var tween := create_tween()
	if fade_out:
		tween.tween_property(fade, "color:a", 1.0, FADE_HALF_TIME)
	else:
		fade.color.a = 1.0
	_tween_hold(tween)
	tween.tween_callback(func() -> void:
		_instantiate_area(area_id, from_area)
		title_layer.visible = false
		background.visible = false
		story_layer.visible = true
		dialog_panel.visible = false
		_clear_choices()
	)
	tween.tween_property(fade, "color:a", 0.0, FADE_HALF_TIME)
	tween.tween_callback(func() -> void:
		if area.has("intro") and not GameState.seen_intros.has(area_id):
			GameState.seen_intros[area_id] = true
			_show_area_text(area["intro"])
		else:
			_begin_explore()
	)


## 離開區域：淡出 → 釋放區域 → 顯示 Background → 回到視覺小說流程的 next_id。
func leave_area(next_id: int) -> void:
	state = State.TRANSITION
	_area.set_can_move(false)
	prompt_label.visible = false
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 1.0, FADE_HALF_TIME)
	_tween_hold(tween)
	tween.tween_callback(func() -> void:
		_free_area()
		background.visible = true
		dialog_panel.visible = true
		scene_title.text = ""
		body.text = ""
		show_scene(next_id, false)
	)


## 互動點目前的內容：依 GameState 套用 variants。
func _area_point(point_id: String) -> Dictionary:
	var raw: Dictionary = areas.get_area(_area_id).get("points", {}).get(point_id, {})
	return AreaData.view(raw, GameState)


## 互動點現在能不能觸發：require 不符合、或 once 且（這個 variant）已完成時不反應。
func _point_active(point_id: String, point: Dictionary) -> bool:
	if point.is_empty() or not AreaData.is_available(point, GameState):
		return false
	var done: bool = GameState.has_flag(AreaData.done_key(_point_key(point_id), point))
	return not (AreaData.is_once(point) and done)


## 可操作狀態：隱藏對話框，讓主角可以移動。
func _begin_explore() -> void:
	state = State.EXPLORE
	dialog_panel.visible = false
	continue_label.visible = false
	_area.set_can_move(true)
	_area.player.end_action()  # 調查完：手放下
	_update_prompt()
	if not _gesture_hint_shown:
		_show_gesture_hint()


func _update_prompt() -> void:
	var point := _area_point(_nearby_point) if not _nearby_point.is_empty() else {}
	if state != State.EXPLORE or not _point_active(_nearby_point, point):
		prompt_label.visible = false
		return
	var label: String = point.get("label", "調查")
	if point.get("type") == "hide" and _area.player.in_cover:
		label = "出來"
	prompt_label.text = "E　%s" % label
	prompt_label.visible = true
	_place_prompt()


## 互動提示浮在主角頭上（A1.5：主角可以往畫面外側走，固定在畫面下方會擋路）
func _place_prompt() -> void:
	if _area == null or not prompt_label.visible:
		return
	var head: Vector2 = _area.player_head_screen()
	var pos := head + Vector2(-prompt_label.size.x / 2.0, -PROMPT_GAP - prompt_label.size.y)
	pos.x = clampf(pos.x, 0.0, BASE_SIZE.x - prompt_label.size.x)
	prompt_label.position = pos


func _on_point_entered(point_id: String) -> void:
	var point := _area_point(point_id)
	if AreaData.trigger_of(point) == "approach":
		# 接近類：走進範圍自動觸發（遇到人的時候）
		if state == State.EXPLORE and _point_active(point_id, point):
			_show_area_text(point, point_id)
		return
	_nearby_point = point_id
	_update_prompt()


func _on_point_exited(point_id: String) -> void:
	if _nearby_point == point_id:
		_nearby_point = ""
		_update_prompt()


## 區域文字：沿用對話框與打字機。choice 打完字後顯示選項，其他類型顯示「點擊繼續」。
## 調查、撿東西的數值效果在打開時套用（同一個互動點一輪只算一次）。
func _show_area_text(holder: Dictionary, point_id := "") -> void:
	var resolved := AreaData.text_of(story, holder)
	_closing_point = point_id
	_closing_view = holder
	_impulse_released = false
	if not point_id.is_empty() and AreaData.trigger_of(holder) == "approach":
		camera_fx.push_in()  # 遇到人：鏡頭輕微推近，關閉文字時退回
	if not point_id.is_empty():
		_area.point_event(point_id, true)
		if holder.get("type") != "exit":
			play_sound(holder.get("sfx", TYPE_SFX.get(holder.get("type"), "")))  # 調查翻找、撿起
	if not point_id.is_empty() and holder.get("type") != "choice":
		GameState.apply_effects(holder.get("effects", {}), AreaData.done_key(_point_key(point_id), holder))
	_area.set_can_move(false)
	prompt_label.visible = false
	_gesture_hint.visible = false  # 按鍵提示不要疊在對話框上
	dialog_panel.visible = true
	ending_tag.visible = false
	hint.visible = false
	continue_label.visible = false
	_clear_choices()
	scene_title.text = resolved.get("title", "")
	if holder.get("type") == "choice":
		var after_text := _show_area_choices.bind(holder.get("choices", []))
		if holder.has("resist") and not point_id.is_empty():
			after_text = _begin_resist.bind(holder["resist"])  # A5：先抵抗衝動，才出現選項
		_type_text(resolved.get("text", ""), after_text)
	else:
		_type_text(resolved.get("text", ""), _show_area_continue)


func _show_area_continue() -> void:
	state = State.AREA_TEXT
	var item_name: String = _area_choice.get("item_name", _closing_view.get("item_name", "") if _closing_view.get("type") == "item" else "")
	if not item_name.is_empty():
		hint.text = "[color=%s]（獲得：%s）[/color]" % [EXTRA_HINT_COLOR, item_name]
		hint.visible = true
	continue_label.visible = true


## 區域的選項：沿用視覺小說的按鈕；自動選好第一個，可以用方向鍵與 Enter／空白鍵操作（可走動區域只用鍵盤）。
func _show_area_choices(choices: Array) -> void:
	state = State.CHOOSING
	_area_choosing = true
	_chosen_in_scene.clear()
	_build_choices(choices)


func _on_area_choice_pressed(choice: Dictionary, by_player := true) -> void:
	_area_choosing = false
	_area_choice = choice
	_impulse_released = true  # 選完了：張力淡出
	hint.visible = false      # 抵抗成功的那一句
	if by_player:
		play_ui("ui_confirm")
	play_sound(choice.get("sfx", ""))  # 例如撲上去的低吼
	if choice.has("item"):
		play_sound("pickup")
	_camera_cue(choice)
	if choice.has("figure"):
		_area.point_play(_closing_point, choice["figure"])  # 例如女兒舉手比出同樣的手勢
	_clear_choices()
	GameState.apply_effects(choice.get("effects", {}), AreaData.done_key(_point_key(_closing_point), _closing_view))
	for flag in choice.get("set_flags", []):
		GameState.set_flag(flag)
	if choice.has("item"):
		GameState.add_item(choice["item"])  # 例如收下女科學家的筆記本
	_type_text(choice.get("response", ""), _show_area_continue)


func _close_area_text() -> void:
	var point_id := _closing_point
	var point := _closing_view
	camera_fx.release()
	_closing_point = ""
	_closing_view = {}
	hint.visible = false
	if point_id.is_empty():  # 開場文字
		_begin_explore()
		return
	_mark_done(point_id)
	_area.point_event(point_id, false)
	GameState.set_flag(AreaData.done_key(_point_key(point_id), point))  # variant 自己的完成紀錄
	if point.get("type") == "item" and point.has("item"):
		GameState.add_item(point["item"])
	for flag in point.get("set_flags", []):
		GameState.set_flag(flag)
	if _hides_when_done(point):
		_area.consume_point(point_id, _area.player_x())  # 例如婦人尖叫、逃走後消失
		play_sound(point.get("done_sfx", ""))  # 例如婦人的尖叫
	var chosen := _area_choice
	_area_choice = {}
	if chosen.has("to"):
		_go_to(chosen["to"])  # 例如警衛逼近時選「停下不動」→ Bad End
		return
	if point.get("type") == "hide" and point.has("to_x"):
		_go_through_vent(point)  # A5 躲藏：鑽進通風管，從另一頭爬出來
		return
	if point.get("type") == "exit":
		_go_through_exit(point)
		return
	_begin_explore()


## 互動點觸發過後設定自動旗標「區域.互動點」（同一輪記得，換區域、回頭走都有效）。
func _mark_done(point_id: String) -> void:
	GameState.set_flag(_point_key(point_id))


func _is_done(point_id: String) -> bool:
	return GameState.has_flag(_point_key(point_id))


## 互動點在整個遊戲中的代號「區域.互動點」：自動旗標與數值效果的來源都用它。
func _point_key(point_id: String) -> String:
	return "%s.%s" % [_area_id, point_id]


## 完成後要隱藏場景中人物或道具的互動點：hide_on_done，或 Lv1 格式的 approach（婦人）。
func _hides_when_done(point: Dictionary) -> bool:
	return point.get("hide_on_done", point.get("type") == "approach")


## 出口：通往另一個區域（to.area），或接回視覺小說（to.scene／Lv1 的 exit_to）。
func _go_through_exit(point: Dictionary) -> void:
	if point.has("sfx"):
		play_sound(point["sfx"])  # 例如推開鐵門：畫面變暗時響起，在黑畫面停一下再進新區域
		_hold_black = SOUND_HOLD_TIME
	_go_to(AreaData.exit_target(areas.get_area(_area_id), point))


## 從區域前往 { "area": id }（另一個區域）或 { "scene": id }（視覺小說／Bad End）。
func _go_to(target: Dictionary) -> void:
	if target.has("area"):
		_switch_area(target["area"])
	elif target.has("scene"):
		leave_area(int(target["scene"]))


## 區域之間移動：記住從哪裡來，決定在新區域的出現位置。
func _switch_area(next_area: String) -> void:
	var from_area := _area_id
	_area.set_can_move(false)
	prompt_label.visible = false
	enter_area(next_area, -1, true, from_area)


## 換曲：與目前曲目相同時不重播；不同時舊曲淡出、新曲淡入。
func play_bgm(file: String) -> void:
	if file == _bgm_file:
		return
	_bgm_file = file
	var old := bgm_players[_bgm_index]
	_bgm_index = 1 - _bgm_index
	var new := bgm_players[_bgm_index]
	if _bgm_tween:
		_bgm_tween.kill()
	new.stop()
	new.stream = load(StoryData.bgm_path(file))
	new.volume_linear = 0.0
	new.play()
	_bgm_tween = create_tween().set_parallel()
	_bgm_tween.tween_property(new, "volume_linear", 1.0, BGM_FADE_TIME)
	if old.playing:
		_bgm_tween.tween_property(old, "volume_linear", 0.0, BGM_FADE_TIME)
		_bgm_tween.chain().tween_callback(old.stop)


## A4：區域環境音（循環），和 BGM 一樣兩個播放器交替淡入淡出；file 為空字串時淡出。
func play_ambience(file: String) -> void:
	if file == _amb_file:
		return
	_amb_file = file
	var old := amb_players[_amb_index]
	_amb_index = 1 - _amb_index
	var new := amb_players[_amb_index]
	if _amb_tween:
		_amb_tween.kill()
	_amb_tween = create_tween().set_parallel()
	if not file.is_empty():
		new.stream = load(SoundLib.SFX_DIR + file)
		new.volume_linear = 0.0
		new.play()
		_amb_tween.tween_property(new, "volume_linear", 1.0, AMB_FADE_TIME)
	if old.playing:
		_amb_tween.tween_property(old, "volume_linear", 0.0, AMB_FADE_TIME)
		_amb_tween.chain().tween_callback(old.stop)


## 轉場時在黑畫面多停 _hold_black 秒（用一次就歸零）
func _tween_hold(tween: Tween) -> void:
	if _hold_black > 0.0:
		tween.tween_interval(_hold_black)
		_hold_black = 0.0


## A4：播放音效（資料的 "sfx"，例如 "growl" 會從 growl_1、growl_2 隨機挑；寫成陣列時同時播放，例如 ["growl", "scream"]）。
## 空字串或找不到時不播。
func play_sound(sound, volume_db := 0.0) -> void:
	if sound is Array:
		for one in sound:
			_play_on(event_sfx, str(one), volume_db)
	else:
		_play_on(event_sfx, str(sound), volume_db)


func play_ui(sound_name: String) -> void:
	_play_on(ui_sfx, sound_name, -6.0)


func _play_on(player: AudioStreamPlayer, sound_name: String, volume_db: float) -> void:
	var stream := SoundLib.pick(sound_name)
	if stream == null:
		return
	sound_log.append(sound_name)
	if sound_log.size() > 20:
		sound_log.pop_front()
	var pool: Array = _pools.get(player, [player])
	var free_player: AudioStreamPlayer = pool[0]
	for p in pool:
		if not (p as AudioStreamPlayer).playing:
			free_player = p
			break
	free_player.stream = stream
	free_player.volume_db = volume_db
	free_player.play()


## 方向鍵移動選項時的游標聲（自動聚焦第一個選項時不出聲）
func _on_choice_focus() -> void:
	if not _quiet_focus:
		play_ui("ui_cursor")


func show_scene(id: int, fade_out := true) -> void:
	var scene := story.get_scene(id)
	if scene.is_empty():
		return
	# 被區域接管的場景：改成進入可走動的區域，不顯示視覺小說畫面
	var area := areas.area_for_scene(id)
	if not area.is_empty():
		enter_area(area["id"], id, fade_out)
		return
	_clear_choices()
	hint.visible = false
	continue_label.visible = false
	dialog_panel.visible = true

	if id == current_id:
		# 留在原場景：已讀過的主文字直接完整顯示，重新給選項。
		body.text = scene["text"]
		body.visible_ratio = 1.0
		_show_choices(scene)
		return

	current_id = id
	_chosen_in_scene.clear()
	if not scene.get("is_ending", false):
		_save_checkpoint({ "scene": id })
	state = State.TRANSITION
	play_bgm(scene["bgm"])
	play_ambience("")  # 過場與結局沒有區域環境音
	var tween := create_tween()
	if fade_out:
		tween.tween_property(fade, "color:a", 1.0, FADE_HALF_TIME)
	else:
		fade.color.a = 1.0
	tween.tween_callback(func() -> void:
		background.texture = load(StoryData.bg_path(scene["bg"]))
		scene_title.text = scene["title"]
		ending_tag.visible = scene.get("is_ending", false)
		ending_tag.text = scene.get("ending_label", ENDING_LABEL)
		var bad: bool = scene.get("ending_type", "normal") == "bad"
		ending_tag.add_theme_color_override("font_color", BAD_ENDING_COLOR if bad else Color(1, 1, 1))
		body.text = ""
		play_sound(scene.get("sfx", ""))  # 例如槍聲、撞上鐵絲網：在黑畫面中響起
	)
	if scene.has("sfx"):
		tween.tween_interval(SOUND_HOLD_TIME)
	tween.tween_property(fade, "color:a", 0.0, FADE_HALF_TIME)
	tween.tween_callback(func() -> void:
		_camera_cue(scene)  # 例如 Bad End「槍聲」：淡入後畫面震動
		_type_text(scene["text"], _show_choices.bind(scene))
	)


## 資料裡的鏡頭提示（A2-4）：選項或場景寫 "camera": "shake" 時畫面震動（撲上去、槍聲）。
func _camera_cue(holder: Dictionary) -> void:
	if holder.get("camera", "") == "shake":
		camera_fx.shake()


func _show_choices(scene: Dictionary) -> void:
	state = State.CHOOSING
	_show_hint(scene)
	_build_choices(scene["choices"])


func _show_hint(scene: Dictionary) -> void:
	var text: String = scene.get("hint", "")
	var extra: String = scene.get("extra_hint", "")
	if not extra.is_empty():
		text += "\n[color=%s]%s[/color]" % [EXTRA_HINT_COLOR, extra]
	hint.text = text
	hint.visible = not text.is_empty()


func _build_choices(choices: Array) -> void:
	_clear_choices()
	for i in choices.size():
		var choice: Dictionary = choices[i]
		var button := Button.new()
		button.text = choice["text"]
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.add_theme_font_size_override("font_size", 20)
		for style_name in _button_styles:
			button.add_theme_stylebox_override(style_name, _button_styles[style_name])
		if _chosen_in_scene.has(i):
			button.modulate = CHOSEN_MODULATE
		if choice.has("require") and not GameState.meets(choice["require"]):
			# 數值不夠：顯示灰色「……（你想不起來）」，不能選
			button.text = choice.get("locked_text", LOCKED_TEXT)
			button.disabled = true
			button.add_theme_stylebox_override("disabled", _button_styles["disabled"])
			button.add_theme_color_override("font_disabled_color", Color(0.55, 0.55, 0.55))
			button.focus_mode = Control.FOCUS_NONE  # 方向鍵移動時跳過鎖住的選項
		button.pressed.connect(_on_choice_pressed.bind(i, choice))
		button.focus_entered.connect(_on_choice_focus)
		choices_box.add_child(button)
	# 鍵盤操作：聚焦第一個能選的選項（方向鍵移動、Enter／空白鍵選擇）。
	# 打開選項的那次按鍵已經 set_input_as_handled()，不會同時按下這個選項；
	# 打字自然結束時剛好按下的鍵，則由 CHOICE_GUARD_MS 擋掉。
	_choices_shown_at = Time.get_ticks_msec()
	for button in choices_box.get_children():
		if not (button as Button).disabled:
			_quiet_focus = true
			(button as Button).grab_focus()
			_quiet_focus = false
			break


func _clear_choices() -> void:
	for child in choices_box.get_children():
		choices_box.remove_child(child)
		child.queue_free()


## 打字機效果：逐字增加 visible_characters，結束後呼叫 on_done。
func _type_text(text: String, on_done: Callable) -> void:
	state = State.TYPING
	_after_typing = on_done
	body.text = text
	body.visible_characters = 0
	_typed_text = body.get_parsed_text()
	_typed_count = 0
	_next_tick_at = 1
	if _typing_tween:
		_typing_tween.kill()
	_typing_tween = create_tween()
	_typing_tween.tween_method(_set_typed_count, 0, _typed_text.length(),
			_typed_text.length() / CHARS_PER_SECOND)
	_typing_tween.tween_callback(_finish_typing)


func _set_typed_count(count: int) -> void:
	body.visible_characters = count
	while _typed_count < count:
		_typed_count += 1
		if _typed_count >= _next_tick_at:
			_play_type_tick(_typed_text[_typed_count - 1])


## 鍵盤感：每 2～4 個字隨機響一次，音高與音量帶些微變化，標點與空白不出聲。
func _play_type_tick(ch: String) -> void:
	if not GameSettings.get_value("typing"):  # A6：設定裡的打字聲開關（預設關）
		return
	if SILENT_CHARS.contains(ch):
		_next_tick_at = _typed_count + 1  # 標點後的下一個字馬上出聲，形成停頓後的重音
		return
	_next_tick_at = _typed_count + randi_range(2, 4)
	type_sfx.pitch_scale = randf_range(0.85, 1.25)
	type_sfx.volume_db = _type_base_db + randf_range(-4.0, 1.0)
	type_sfx.play()


func _finish_typing() -> void:
	if state != State.TYPING:
		return
	if _typing_tween:
		_typing_tween.kill()
		_typing_tween = null
	body.visible_characters = -1
	type_sfx.stop()  # 文字全部顯示後立即停止打字聲
	_after_typing.call()


func _on_choice_pressed(index: int, choice: Dictionary) -> void:
	if state != State.CHOOSING or not choices_ready():
		return
	if _area_choosing:
		_on_area_choice_pressed(choice)
		return
	_chosen_in_scene[index] = true
	play_ui("ui_confirm")
	play_sound(choice.get("sfx", ""))
	_camera_cue(choice)
	_clear_choices()
	hint.visible = false
	_pending_choice = choice
	_pending_next_id = int(choice.get("next_id", -1))
	GameState.apply_effects(choice.get("effects", {}), "scene.%d" % current_id)  # 同一個場景一輪只算一次
	if str(choice.get("response", "")).is_empty():
		_resolve_choice()  # 沒有回應文字（例如 Bad End 的「從這裡重試」）時直接前往
		return
	_type_text(choice["response"], _show_continue)


## 選項出現超過 CHOICE_GUARD_MS 才能選（測試也用這個判斷什麼時候可以按）
func choices_ready() -> bool:
	return Time.get_ticks_msec() - _choices_shown_at >= CHOICE_GUARD_MS


## 視覺小說的選項讀完回應後的去處：action（retry／title）> next_area > 結局回標題 > next_id。
func _resolve_choice() -> void:
	var choice := _pending_choice
	_pending_choice = {}
	continue_label.visible = false
	match choice.get("action", ""):
		"retry":
			_retry()
		"title":
			_return_to_title()
		_:
			if choice.has("next_area"):
				enter_area(choice["next_area"], -1, true)
			elif story.get_scene(current_id).get("is_ending", false):
				_return_to_title()  # 1.0 格式的結局：選「重新開始」回到標題畫面
			else:
				# next_id 等於目前場景時（例如「停留不動」）會重新顯示同一場景的選項。
				show_scene(_pending_next_id)


## 檢查點：進入區域或非結局的過場時存一份（位置＋完整狀態），Bad End 重試時還原。
func _save_checkpoint(place: Dictionary) -> void:
	_checkpoint = place.duplicate()
	_checkpoint["state"] = GameState.snapshot()


func _retry() -> void:
	if _checkpoint.is_empty():
		_return_to_title()
		return
	GameState.restore(_checkpoint["state"])
	current_id = -1
	if _checkpoint.has("area"):
		enter_area(_checkpoint["area"], -1, true, _checkpoint.get("from", ""))
	else:
		show_scene(int(_checkpoint["scene"]))


func _show_continue() -> void:
	state = State.RESPONSE
	continue_label.visible = true


## A5 壓抑衝動：事件文字打完後出現「連打【空白鍵】抵抗」與量表。連打會漲、平常會掉、每次心跳被拉掉一點，時限內漲滿就成功。
func _begin_resist(resist: Dictionary) -> void:
	state = State.RESIST
	_resist = resist
	resist_value = 0.0
	_resist_left = float(resist.get("time", RESIST_TIME))
	resist_label.text = story.resist_prompt_hold if RESIST_HOLD else story.resist_prompt
	resist_bar.value = 0.0
	resist_box.visible = true


## 成功：撲上去類的選項（fail）隱藏、顯示一句，再出現選項。失敗：自動撲上去（等於選了 fail 那個選項）。
func _finish_resist(success: bool) -> void:
	if state != State.RESIST:
		return
	state = State.TRANSITION
	resist_box.visible = false
	_input_locked_until = Time.get_ticks_msec() + RESIST_LOCK_MS
	var choices: Array = _closing_view.get("choices", [])
	var fail := int(_resist.get("fail", 0))
	if success:
		_impulse_released = true  # 衝動退去：紅色、心跳淡出
		hint.text = story.resist_success
		hint.visible = true
		var rest := choices.duplicate()
		rest.remove_at(fail)
		await get_tree().create_timer(RESIST_LOCK_MS / 1000.0).timeout
		while Input.is_action_pressed("interact"):  # 按住的玩家要先放開，選項才出現（避免一出現就被選到）
			await get_tree().process_frame
		_show_area_choices(rest)
	else:
		_on_area_choice_pressed(choices[fail], false)


## 抵抗中每次心跳，量表被拉掉一點
func _on_heartbeat() -> void:
	if state == State.RESIST:
		resist_value = maxf(resist_value - RESIST_TUG, 0.0)


## 測試用：目前抵抗的失敗選項是第幾個
func resist_fail_index() -> int:
	return int(_resist.get("fail", -1)) if state == State.RESIST else -1


## A5 躲藏：區域裡有 patrol 的互動點（警衛），在它底下建立巡視節點
func _setup_patrols() -> void:
	patrols.clear()
	var points: Dictionary = areas.get_area(_area_id).get("points", {})
	for point_id in points:
		if not points[point_id].has("patrol"):
			continue
		var node: Node = _area.point_node(point_id)
		if node == null or not node.has_node("Figure") or not node.has_node("Torch"):
			continue
		var patrol := GuardPatrol.new()
		patrol.name = "Patrol"
		node.add_child(patrol)
		patrol.setup(points[point_id]["patrol"], node.get_node("Figure"), node.get_node("Torch"), _area.player)
		patrol.spotted.connect(_on_spotted.bind(point_id))
		patrols[point_id] = patrol


## 被警衛發現：轉向主角、上膛聲、畫面震動，進入原本的事件（旗標「區域.互動點.spotted」讓事件換成被發現的文字）
func _on_spotted(point_id: String) -> void:
	if state != State.EXPLORE:
		return
	GameState.set_flag(_point_key(point_id) + ".spotted")
	_area.player.set_in_cover(false)
	patrols[point_id].face_toward(_area.player_x())
	play_sound(SPOTTED_SFX)
	camera_fx.shake()
	_show_area_text(_area_point(point_id), point_id)


## 躲到掩護後面／出來
func _toggle_hidden() -> void:
	var player = _area.player
	player.set_in_cover(not player.in_cover)
	if player.in_cover:
		play_sound(HIDE_SFX)
	_update_prompt()


## 鑽進通風管：黑畫面 → 從另一頭（to_x）爬出來，done 指定的事件（警衛）一起結束 → 顯示 after_text
func _go_through_vent(point: Dictionary) -> void:
	state = State.TRANSITION
	_area.set_can_move(false)
	prompt_label.visible = false
	_area.player.set_in_cover(false)
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 1.0, FADE_HALF_TIME)
	tween.tween_interval(SOUND_HOLD_TIME)
	tween.tween_callback(func() -> void:
		_area.place_player(float(point["to_x"]))
		_area.player.face(1)
		if point.has("done"):
			_finish_point(str(point["done"]))
	)
	tween.tween_property(fade, "color:a", 0.0, FADE_HALF_TIME)
	tween.tween_callback(func() -> void:
		_show_area_text({ "title": point.get("title", ""), "text": point.get("after_text", "") })
	)


## 讓互動點的事件直接算結束（不顯示文字）：完成旗標、人物離開
func _finish_point(point_id: String) -> void:
	var point := _area_point(point_id)
	_mark_done(point_id)
	GameState.set_flag(AreaData.done_key(_point_key(point_id), point))
	_area.consume_point(point_id)


## A5：區域的 hint（{ after_x, text }）：主角第一次走過 after_x 時，畫面下方淡淡顯示一次
func _check_area_hint() -> void:
	if state != State.EXPLORE or _area == null:
		return
	var hint_data: Dictionary = areas.get_area(_area_id).get("hint", {})
	if hint_data.is_empty() or _area.player_x() < float(hint_data.get("after_x", 0.0)):
		return
	var key := "hint.%s" % _area_id
	if GameState.has_flag(key):
		return
	GameState.set_flag(key)
	_show_bottom_hint(str(hint_data.get("text", "")))


## 打開互動點：有記憶閃回（flashback）而且這一輪還沒閃回過時，先閃回再顯示文字。
func _open_point(point: Dictionary, point_id: String) -> void:
	if point.has("flashback") and not GameState.has_flag(_point_key(point_id) + ".flashback"):
		await _play_flashback(str(point["flashback"]), point_id)
	_show_area_text(point, point_id)


## A5 記憶閃回：白光一閃 → 原插畫（褪色、雜訊、暗角）停 FLASHBACK_TIME 秒 → 淡出淡入回到區域。按互動鍵可以跳過。
func _play_flashback(image: String, point_id: String) -> void:
	state = State.FLASHBACK
	_flashback_ending = false
	_area.set_can_move(false)
	prompt_label.visible = false
	GameState.set_flag(_point_key(point_id) + ".flashback")
	_gesture_hint.visible = false  # 按鍵提示不要蓋在閃回畫面上
	play_sound("flashback")
	flashback.texture = load(StoryData.bg_path(image))
	_flashback_tween = create_tween()
	_flashback_tween.tween_property(flash, "color:a", 1.0, FLASHBACK_FLASH)
	_flashback_tween.tween_callback(func() -> void: flashback.visible = true)
	_flashback_tween.tween_property(flash, "color:a", 0.0, FLASHBACK_REVEAL)
	_flashback_tween.tween_interval(FLASHBACK_TIME)
	_flashback_tween.tween_callback(_end_flashback)
	await flashback_finished


## 閃回結束（播完或跳過）：淡出到黑、收起插畫、淡入回到區域
func _end_flashback() -> void:
	if _flashback_ending:
		return
	_flashback_ending = true
	if _flashback_tween:
		_flashback_tween.kill()
	var tween := create_tween()
	tween.tween_property(flash, "color:a", 0.0, 0.05)
	tween.tween_property(fade, "color:a", 1.0, FLASHBACK_FADE)
	tween.tween_callback(func() -> void: flashback.visible = false)
	tween.tween_property(fade, "color:a", 0.0, FLASHBACK_FADE)
	tween.tween_callback(func() -> void: flashback_finished.emit())


## A5：比出手勢「我——在——這——裡」。附近有會反應的人（互動點的 gesture）就在比完後顯示反應文字（每人一輪一次）；
## 沒有對象時，一輪的第一次顯示獨白（story.json 的 gesture_alone），之後只有動畫。
func _do_gesture() -> void:
	state = State.GESTURE
	_area.set_can_move(false)
	prompt_label.visible = false
	var target := gesture_target()
	play_sound(GESTURE_SFX)
	await _area.player.play_gesture(_area.point_x(target) if not target.is_empty() else NAN)
	if _area == null or state != State.GESTURE:
		return
	var holder := {}
	if not target.is_empty():
		var point := _area_point(target)
		var gesture: Dictionary = point["gesture"]
		var key := _point_key(target) + ".gesture"
		GameState.set_flag(key)  # 之後的事件可以用 variants 依這個旗標換文字
		GameState.apply_effects(gesture.get("effects", {}), key)
		holder = { "title": point.get("title", ""), "text": gesture["text"] }
	elif not GameState.has_flag("gesture.alone") and not story.gesture_alone.is_empty():
		GameState.set_flag("gesture.alone")
		holder = { "title": "", "text": story.gesture_alone }
	if holder.is_empty():
		_begin_explore()
	else:
		_show_area_text(holder)  # 沒有 point_id：關閉後回到探索


## 手勢的對象：有 gesture、事件還沒發生、還沒對他比過、在範圍內的互動點中最近的一個；沒有時回傳空字串。
func gesture_target() -> String:
	var best := ""
	var best_d := INF
	var points: Dictionary = areas.get_area(_area_id).get("points", {})
	for point_id in points:
		if not points[point_id].has("gesture"):
			continue
		var point := _area_point(point_id)
		if not _point_active(point_id, point) or GameState.has_flag(_point_key(point_id) + ".gesture"):
			continue
		var x: float = _area.point_x(point_id)
		var d := absf(x - _area.player_x())
		if d <= float(point["gesture"].get("range", GESTURE_RANGE)) and d < best_d:
			best = point_id
			best_d = d
	return best


func _create_gesture_hint() -> void:
	_gesture_hint = Label.new()
	_gesture_hint.name = "GestureHint"
	_gesture_hint.text = GESTURE_HINT
	_gesture_hint.add_theme_font_size_override("font_size", 18)
	_gesture_hint.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85))
	_gesture_hint.add_theme_color_override("font_outline_color", Color.BLACK)
	_gesture_hint.add_theme_constant_override("outline_size", 4)
	_gesture_hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_gesture_hint.visible = false
	prompt_label.get_parent().add_child(_gesture_hint)
	# 錨點和位移都要設（只設錨點時位移是 0，會跑到左上角）：畫面下方中間、離底部 24 px
	_gesture_hint.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM, Control.PRESET_MODE_MINSIZE, 24)


## 第一次可以走動時，畫面下方淡淡顯示一次按鍵提示，幾秒後淡出
func _show_gesture_hint() -> void:
	_gesture_hint_shown = true
	_show_bottom_hint(GESTURE_HINT)


## 畫面下方淡淡顯示一句提示，幾秒後淡出（手勢、躲藏共用）
func _show_bottom_hint(text: String) -> void:
	_gesture_hint.text = text
	_gesture_hint.visible = true
	_gesture_hint.modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(_gesture_hint, "modulate:a", 0.8, 0.6)
	tween.tween_interval(GESTURE_HINT_TIME)
	tween.tween_property(_gesture_hint, "modulate:a", 0.0, 0.8)
	tween.tween_callback(func() -> void: _gesture_hint.visible = false)


## A6：標題選單與設定面板
func _setup_title_menu() -> void:
	for button in [start_button, settings_button, credits_button, back_button, credits_back]:
		_style_menu_button(button)
	_style_menu_button(typing_toggle, false)  # 開關的 ▶ 加在那一列的名稱上
	typing_toggle.add_theme_font_size_override("font_size", 22)
	for label in music_slider.get_parent().get_children():
		if label is Label:
			label.add_theme_font_size_override("font_size", 22)  # 每一列的名稱、百分比和開關一樣大
	for button in [start_button, settings_button, credits_button]:
		button.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))  # 標題背景是亮的牆，加陰影比較好讀
		button.add_theme_constant_override("shadow_offset_x", 2)
		button.add_theme_constant_override("shadow_offset_y", 2)
	start_button.pressed.connect(_on_title_button.bind("start"))
	settings_button.pressed.connect(_on_title_button.bind("settings"))
	back_button.pressed.connect(_close_settings)
	credits_button.pressed.connect(_on_title_button.bind("credits"))
	credits_back.pressed.connect(_close_credits)
	typing_toggle.pressed.connect(_on_typing_toggled)
	_sliders = { "music": music_slider, "sfx": sfx_slider, "ambient": ambient_slider }
	for key in _sliders:
		var slider: HSlider = _sliders[key]
		slider.value_changed.connect(_on_volume_changed.bind(key))
		_highlight_row_on_focus(slider)
	_highlight_row_on_focus(typing_toggle)
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color(0.07, 0.07, 0.09, 0.94)
	panel_style.border_color = Color(0.35, 0.31, 0.25)
	panel_style.set_border_width_all(2)
	panel_style.set_corner_radius_all(10)
	panel_style.set_content_margin_all(28)
	settings_panel.add_theme_stylebox_override("panel", panel_style)
	credits_panel.add_theme_stylebox_override("panel", panel_style)
	var track := StyleBoxFlat.new()
	track.bg_color = Color(1, 1, 1, 0.15)
	track.set_corner_radius_all(6)
	track.content_margin_top = 6
	track.content_margin_bottom = 6
	var fill := track.duplicate() as StyleBoxFlat
	fill.bg_color = Color(0.78, 0.75, 0.69)
	for slider in _sliders.values():
		slider.add_theme_stylebox_override("slider", track)
		slider.add_theme_stylebox_override("grabber_area", fill)
		slider.add_theme_stylebox_override("grabber_area_highlight", fill)


## 選單按鈕：沒有底框，文字灰色，選中（聚焦或滑鼠移過去）變金色、前面加 ▶
func _style_menu_button(button: Button, with_arrow := true) -> void:
	var empty := StyleBoxEmpty.new()
	for style_name in ["normal", "hover", "pressed", "focus", "disabled"]:
		button.add_theme_stylebox_override(style_name, empty)
	button.add_theme_font_size_override("font_size", 24)
	button.add_theme_color_override("font_color", MENU_COLOR)
	for color_name in ["font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]:
		button.add_theme_color_override(color_name, MENU_FOCUS_COLOR)
	if with_arrow:
		button.set_meta("base_text", button.text)
		button.focus_entered.connect(func() -> void:
			button.text = "▶ " + str(button.get_meta("base_text"))
			_on_choice_focus())
		button.focus_exited.connect(func() -> void: button.text = str(button.get_meta("base_text")))
	button.mouse_entered.connect(func() -> void:
		if button.is_visible_in_tree():
			button.grab_focus())


## 設定面板裡，聚焦的那一列名稱變金色、前面加 ▶
func _highlight_row_on_focus(control: Control) -> void:
	var label := control.get_parent().get_child(control.get_index() - 1) as Label
	var base := label.text
	control.focus_entered.connect(func() -> void:
		label.text = "▶ " + base
		label.add_theme_color_override("font_color", MENU_FOCUS_COLOR)
		_on_choice_focus())
	control.focus_exited.connect(func() -> void:
		label.text = base
		label.remove_theme_color_override("font_color"))


## 標題畫面的按鍵：第一次按鍵或點擊時解鎖聲音、開始播標題曲（瀏覽器規定互動後才能播放）；設定面板開著時 Esc 關閉
func _title_input(event: InputEvent) -> void:
	var pressed := (event is InputEventKey or event is InputEventMouseButton) and event.is_pressed()
	if pressed and not _audio_unlocked:
		_audio_unlocked = true
		play_bgm(story.title_screen["bgm"])
	if settings_panel.visible and event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_close_settings()
	elif credits_panel.visible:
		if event.is_action_pressed("ui_cancel"):
			get_viewport().set_input_as_handled()
			_close_credits()
		elif event.is_action_pressed("ui_up", true) or event.is_action_pressed("ui_down", true):
			get_viewport().set_input_as_handled()  # ↑↓ 捲動內容（不移動焦點）
			credits_scroll.scroll_vertical += CREDITS_SCROLL_STEP * (-1 if event.is_action("ui_up") else 1)


func _on_title_button(which: String) -> void:
	if state != State.TITLE:
		return
	play_ui("ui_confirm")
	match which:
		"start":
			_start_game()
		"settings":
			_open_settings()
		"credits":
			_open_credits()


func _open_settings() -> void:
	title_menu.visible = false
	title_label.visible = false  # 標題的字會從面板後面透出來
	settings_panel.visible = true
	for key in _sliders:
		(_sliders[key] as HSlider).set_value_no_signal(roundf(float(GameSettings.get_value(key)) * 100.0))
		_update_volume_label(key)
	_update_typing_text()
	_quiet_focus = true
	music_slider.grab_focus()
	_quiet_focus = false


func _close_settings() -> void:
	settings_panel.visible = false
	title_menu.visible = true
	title_label.visible = true
	play_ui("ui_cancel")
	_quiet_focus = true
	settings_button.grab_focus()
	_quiet_focus = false


func _open_credits() -> void:
	title_menu.visible = false
	title_label.visible = false
	credits_panel.visible = true
	if credits_text.text.is_empty():
		credits_text.text = _credits_bbcode()
	credits_scroll.scroll_vertical = 0
	_quiet_focus = true
	credits_back.grab_focus()
	_quiet_focus = false


func _close_credits() -> void:
	credits_panel.visible = false
	title_menu.visible = true
	title_label.visible = true
	play_ui("ui_cancel")
	_quiet_focus = true
	credits_button.grab_focus()
	_quiet_focus = false


## 製作群的內容：data/credits.json 的各段（標題金色），最後是 Godot Engine 的 MIT 授權全文與第三方元件清單（引擎提供，和實際使用的版本一致）
func _credits_bbcode() -> String:
	var data = JSON.parse_string(FileAccess.get_file_as_string(CREDITS_FILE))
	if typeof(data) != TYPE_DICTIONARY:
		return ""
	var out := ""
	for section in data.get("sections", []):
		out += "[color=#e8cf8a]%s[/color]\n" % _bb_escape(section.get("title", ""))
		for line in section.get("lines", []):
			out += _bb_escape(str(line)) + "\n"
		out += "\n"
	if data.get("engine_license", false):
		out += "[color=#8a8a8a]────────────\n本遊戲使用 Godot Engine，授權如下：[/color]\n"
		out += "[font_size=14]" + _bb_escape(Engine.get_license_text()) + "[/font_size]\n\n"
		out += "[color=#8a8a8a]Godot Engine 使用的第三方元件：[/color]\n[font_size=14]"
		for info in Engine.get_copyright_info():
			var licenses := {}
			for part in info.get("parts", []):
				licenses[part.get("license", "")] = true
			out += "%s（%s）\n" % [_bb_escape(info.get("name", "")), "、".join(licenses.keys())]
		out += "[/font_size]"
	return out


func _bb_escape(text: String) -> String:
	return text.replace("[", "[lb]")


func _on_volume_changed(value: float, key: String) -> void:
	GameSettings.set_value(key, value / 100.0)
	_update_volume_label(key)
	if key == "sfx":
		play_ui("ui_confirm")  # 調音效時播一聲，聽得出大小


func _update_volume_label(key: String) -> void:
	var slider: HSlider = _sliders[key]
	var value_label := slider.get_parent().get_child(slider.get_index() + 1) as Label
	value_label.text = "%d%%" % int(slider.value)


func _on_typing_toggled() -> void:
	GameSettings.set_value("typing", not GameSettings.get_value("typing"))
	_update_typing_text()
	play_ui("ui_confirm")


func _update_typing_text() -> void:
	typing_toggle.text = "開" if GameSettings.get_value("typing") else "關"


## 除錯用：F3 顯示目前的數值（只在 debug 版建立，Web 正式版不會出現）。
func _create_debug_label() -> void:
	_debug_label = Label.new()
	_debug_label.name = "DebugStats"
	_debug_label.position = Vector2(16, 12)
	_debug_label.add_theme_font_size_override("font_size", 18)
	_debug_label.add_theme_color_override("font_color", Color(0.6, 1.0, 0.6))
	_debug_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_debug_label.add_theme_constant_override("outline_size", 4)
	_debug_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_debug_label.visible = false
	add_child(_debug_label)


func _process(delta: float) -> void:
	for point_id in patrols:
		var patrol = patrols[point_id]  # 不指定型別：區域釋放後這裡是已釋放的物件，先檢查再用
		if is_instance_valid(patrol):
			patrol.active = state == State.EXPLORE and _point_active(point_id, _area_point(point_id))
	_check_area_hint()
	if state == State.RESIST:
		if RESIST_HOLD and Input.is_action_pressed("interact"):
			resist_value = minf(resist_value + delta / float(_resist.get("hold", RESIST_HOLD_TIME)), 1.0)
		else:
			resist_value = maxf(resist_value - RESIST_DRAIN * delta, 0.0)
		if resist_value >= 1.0:
			_finish_resist(true)
			return
		_resist_left -= delta
		resist_bar.value = resist_value
		if _resist_left <= 0.0:
			_finish_resist(false)
	impulse_fx.target = _impulse_target()
	camera_fx.sway = impulse_fx.intensity
	if _area:
		_area.player.lean = impulse_fx.intensity >= LEAN_FROM
		_area.player.lean_toward = _impulse_x
	_place_prompt()
	if _debug_label and _debug_label.visible:
		var parts: Array[String] = []
		for key in GameState.stats:
			parts.append("%s %d" % [{ "memory": "記憶", "humanity": "人性" }.get(key, key), GameState.stats[key]])
		_debug_label.text = "【F3】" + "　".join(parts) + ("　物品：" + "、".join(GameState.items.keys()) if not GameState.items.is_empty() else "")


## 衝動機制（甲）的目標強度 0～1：有 impulse 的事件文字或選項打開時最強、選完後歸零；
## 平常依主角與「還沒發生的」有 impulse 的互動點的距離計算，取最近的那個。
func _impulse_target() -> float:
	_impulse_x = NAN
	if _area == null or _area_id.is_empty():
		return 0.0
	if not _closing_point.is_empty() and _closing_view.has("impulse"):
		_impulse_x = _area.point_x(_closing_point)
		return 0.0 if _impulse_released else 1.0
	var player_x: float = _area.player_x()
	var best := 0.0
	var points: Dictionary = areas.get_area(_area_id).get("points", {})
	for point_id in points:
		if not points[point_id].has("impulse"):
			continue
		var point := _area_point(point_id)
		if not _point_active(point_id, point):
			continue  # 事件已經發生（人走了），不再有感覺
		var x: float = _area.point_x(point_id)
		if is_nan(x):
			continue
		var range_px := float(point["impulse"].get("range", impulse_fx.default_range))
		var strength: float = impulse_fx.strength_at(absf(player_x - x), range_px)
		if strength > best:
			best = strength
			_impulse_x = x
	return best


## 除錯用：回傳目前 FPS（給 MCP 的 execute_code 讀取；execute_code 不能直接存取 Engine）。正式版回傳 -1。
func debug_fps() -> float:
	return Engine.get_frames_per_second() if OS.is_debug_build() else -1.0


## 直式畫面（高 > 寬，例如手機直拿）時顯示「請將裝置橫向持握」，並暫停點擊推進。
func _on_window_resized() -> void:
	update_rotate_hint(get_window().size)


func update_rotate_hint(window_size: Vector2i) -> void:
	rotate_hint.visible = window_size.y > window_size.x


func _input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if _debug_label and key and key.pressed and not key.echo and key.keycode == KEY_F3:
		_debug_label.visible = not _debug_label.visible
		get_viewport().set_input_as_handled()
		return
	if rotate_hint.visible:
		get_viewport().set_input_as_handled()
		return
	if Time.get_ticks_msec() < _input_locked_until:
		get_viewport().set_input_as_handled()
		return
	if state == State.RESIST:
		var key_event := event as InputEventKey
		if event.is_action_pressed("interact") and not (key_event and key_event.echo):
			get_viewport().set_input_as_handled()
			if RESIST_HOLD:
				return  # 按住的量表在 _process 處理
			resist_value = minf(resist_value + 1.0 / float(_resist.get("presses", 12)), 1.0)
			if resist_value >= 1.0:
				_finish_resist(true)
		return
	if state == State.FLASHBACK:
		if event.is_action_pressed("interact") or event.is_action_pressed("ui_accept"):
			get_viewport().set_input_as_handled()
			_end_flashback()  # 跳過閃回
		return
	if state == State.EXPLORE and event.is_action_pressed("gesture"):
		get_viewport().set_input_as_handled()
		_do_gesture()
		return
	if state == State.EXPLORE:
		# 同一個輸入事件只處理一次：開啟文字後立即標記為已處理，不會同時被當成「關閉」。
		if event.is_action_pressed("interact") and not _nearby_point.is_empty():
			get_viewport().set_input_as_handled()
			var point := _area_point(_nearby_point)
			if not _point_active(_nearby_point, point):
				return
			if point.get("type") == "hide" and not point.has("to_x"):
				_toggle_hidden()  # A5 躲藏：躲到掩護後面／出來
			elif point.get("type") == "exit" and AreaData.text_of(story, point).is_empty():
				_mark_done(_nearby_point)
				_go_through_exit(point)  # 沒有文字的出口（例如「回到停車場」）直接換區域
			else:
				if point.get("type") != "exit":
					_area.player_reach(_nearby_point)  # A3：轉向物件、伸手調查
				_open_point(point, _nearby_point)
		return
	if state == State.TITLE:
		_title_input(event)  # A6：標題由選單處理（第一次按鍵時解鎖聲音）
		return
	if state != State.TYPING and state != State.RESPONSE and state != State.AREA_TEXT:
		return
	var mb := event as InputEventMouseButton
	var clicked := mb != null and mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT
	if not (clicked or event.is_action_pressed("ui_accept") or event.is_action_pressed("interact")):
		return
	get_viewport().set_input_as_handled()
	if state == State.AREA_TEXT:
		_close_area_text()
	elif state == State.TYPING:
		_finish_typing()  # 打字中點擊：直接顯示全部
	else:
		_resolve_choice()


func _return_to_title() -> void:
	state = State.TRANSITION
	continue_label.visible = false
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 1.0, FADE_HALF_TIME)
	tween.tween_callback(show_title)
