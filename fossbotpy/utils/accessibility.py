#accessibility numbers for science. Pretty sure fosscord just hardcodes this as 128.

class ACCESSIBILITY_FEATURES:
	SCREENREADER = 1 << 0
	REDUCED_MOTION = 1 << 1
	REDUCED_TRANSPARENCY = 1 << 2
	HIGH_CONTRAST = 1 << 3
	BOLD_TEXT = 1 << 4
	GRAYSCALE = 1 << 5
	INVERT_COLORS = 1 << 6
	PREFERS_COLOR_SCHEME_LIGHT = 1 << 7
	PREFERS_COLOR_SCHEME_DARK = 1 << 8
	CHAT_FONT_SCALE_INCREASED = 1 << 9
	CHAT_FONT_SCALE_DECREASED = 1 << 10
	ZOOM_LEVEL_INCREASED = 1 << 11
	ZOOM_LEVEL_DECREASED = 1 << 12
	MESSAGE_GROUP_SPACING_INCREASED = 1 << 13
	MESSAGE_GROUP_SPACING_DECREASED = 1 << 14
	DARK_SIDEBAR = 1 << 15
	REDUCED_MOTION_FROM_USER_SETTINGS = 1 << 16

class Accessibility:
	@staticmethod
	def calculate_accessibility(types):
		accessibility_num = 0
		for i in types:
			feature = i.upper().replace(' ', '_')
			if hasattr(ACCESSIBILITY_FEATURES, feature):
				accessibility_num |= getattr(ACCESSIBILITY_FEATURES, feature)
		return accessibility_num

	@staticmethod
	def check_accessibilities(accessibility_num, check):
		return (accessibility_num & check) == check
