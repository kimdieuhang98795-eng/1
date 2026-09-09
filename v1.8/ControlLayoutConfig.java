package com.ajiu.reva;

/**
 * Pure layout/input metadata for the touch HUD.
 *
 * The original Flash game still receives keyboard semantics, but the mobile HUD
 * no longer hard-codes geometry inside MainActivity. Later versions can persist
 * user-customized positions/sizes without touching the input router.
 */
public final class ControlLayoutConfig {
    public static final String HOLD = "hold";
    public static final String PULSE = "pulse";
    public static final String PAGE = "page";

    public static final class ButtonSpec {
        public final String key;
        public final String caption;
        public final String inputMode;
        public final String category;
        public final int tone;
        public final boolean circle;
        public final float left, top, right, bottom;

        private ButtonSpec(String key, String caption, String inputMode, String category,
                           int tone, boolean circle, float left, float top, float right, float bottom) {
            this.key = key;
            this.caption = caption;
            this.inputMode = inputMode;
            this.category = category;
            this.tone = tone;
            this.circle = circle;
            this.left = left;
            this.top = top;
            this.right = right;
            this.bottom = bottom;
        }

        public static ButtonSpec circle(String key, String caption, String inputMode, String category,
                                        int tone, float cx, float cy, float radius) {
            return new ButtonSpec(key, caption, inputMode, category, tone, true,
                    cx - radius, cy - radius, cx + radius, cy + radius);
        }

        public static ButtonSpec pill(String key, String caption, String inputMode, String category,
                                      int tone, float left, float top, float right, float bottom) {
            return new ButtonSpec(key, caption, inputMode, category, tone, false,
                    left, top, right, bottom);
        }
    }

    public final ButtonSpec[] coreButtons;
    public final ButtonSpec[] skillSlots;
    public final ButtonSpec pageButton;
    public final ButtonSpec[] itemButtons;
    public final ButtonSpec[] utilityButtons;

    public final float joystickHomeX, joystickHomeY, joystickRadius;
    public final float joystickZoneLeft, joystickZoneTop, joystickZoneRight, joystickZoneBottom;
    public final float joystickClampLeft, joystickClampTop, joystickClampRight, joystickClampBottom;

    private ControlLayoutConfig(ButtonSpec[] coreButtons,
                                ButtonSpec[] skillSlots,
                                ButtonSpec pageButton,
                                ButtonSpec[] itemButtons,
                                ButtonSpec[] utilityButtons,
                                float joystickHomeX, float joystickHomeY, float joystickRadius,
                                float joystickZoneLeft, float joystickZoneTop, float joystickZoneRight, float joystickZoneBottom,
                                float joystickClampLeft, float joystickClampTop, float joystickClampRight, float joystickClampBottom) {
        this.coreButtons = coreButtons;
        this.skillSlots = skillSlots;
        this.pageButton = pageButton;
        this.itemButtons = itemButtons;
        this.utilityButtons = utilityButtons;
        this.joystickHomeX = joystickHomeX;
        this.joystickHomeY = joystickHomeY;
        this.joystickRadius = joystickRadius;
        this.joystickZoneLeft = joystickZoneLeft;
        this.joystickZoneTop = joystickZoneTop;
        this.joystickZoneRight = joystickZoneRight;
        this.joystickZoneBottom = joystickZoneBottom;
        this.joystickClampLeft = joystickClampLeft;
        this.joystickClampTop = joystickClampTop;
        this.joystickClampRight = joystickClampRight;
        this.joystickClampBottom = joystickClampBottom;
    }

    /**
     * DNF-Mobile-inspired hierarchy without copying proprietary art assets:
     * one dominant attack button, nearby movement-combat actions, six skill
     * sockets in an arc, and low-frequency items/utilities kept away from the
     * primary thumb cluster.
     */
    public static ControlLayoutConfig modern() {
        ButtonSpec[] core = new ButtonSpec[] {
            ButtonSpec.circle("X", "普攻", HOLD, "attack", 0, 1190, 610, 66),
            ButtonSpec.circle("C", "跳跃", PULSE, "core", 1, 1082, 671, 42),
            ButtonSpec.circle("Z", "上挑", PULSE, "core", 2, 1084, 568, 41),
            ButtonSpec.circle("V", "抓取", PULSE, "core", 3, 982, 651, 39),
            ButtonSpec.circle("↓", "后跳", PULSE, "backstep", 6, 911, 688, 31)
        };

        // key/caption are placeholders here; runtime supplies A..H / Q..Y.
        ButtonSpec[] skills = new ButtonSpec[] {
            ButtonSpec.circle("", "", PULSE, "skill", 4, 990, 510, 35),
            ButtonSpec.circle("", "", PULSE, "skill", 5, 1066, 478, 35),
            ButtonSpec.circle("", "", PULSE, "skill", 6, 1141, 472, 35),
            ButtonSpec.circle("", "", PULSE, "skill", 7, 911, 551, 34),
            ButtonSpec.circle("", "", PULSE, "skill", 8, 916, 469, 34),
            ButtonSpec.circle("", "", PULSE, "skill", 9, 983, 421, 34)
        };

        ButtonSpec page = ButtonSpec.circle("PAGE", "", PAGE, "page", 8, 1214, 392, 31);

        ButtonSpec[] items = new ButtonSpec[] {
            ButtonSpec.circle("1", "", PULSE, "item", 9, 535, 681, 27),
            ButtonSpec.circle("2", "", PULSE, "item", 9, 600, 681, 27),
            ButtonSpec.circle("3", "", PULSE, "item", 9, 665, 681, 27)
        };

        ButtonSpec[] utility = new ButtonSpec[] {
            ButtonSpec.pill("SPACE", "特殊", HOLD, "utility", 7, 714, 651, 792, 701),
            ButtonSpec.pill("SHIFT", "辅助", HOLD, "utility", 7, 803, 651, 881, 701)
        };

        return new ControlLayoutConfig(
                core, skills, page, items, utility,
                154f, 565f, 105f,
                0f, 340f, 390f, 720f,
                92f, 390f, 335f, 625f);
    }
}
