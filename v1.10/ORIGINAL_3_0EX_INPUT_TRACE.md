# Reva 3.0 EX original input trace

Source: pinned `lbmxex.swf` used by the Android build (`17,628,685` bytes, SHA-256 `0c7904469438078919c705dc7d0da11a9e0595fce29decd68f84599b25d3f457`), decompiled with FFDec 26.2.1.

This file records only mappings that are visible in the original AS2. Internal Korean variable names are intentionally preserved where a polished move name has not yet been proven.

## Shared normal controls

- Movement: Left / Right
- Backstep: Down
- Attack: X
- Jump: C
- Up/basic attack: Z
- Grab: V
- Normal skill shortcuts: A S D F G H / Q W E R T Y
- Items used by the wrapper: 1 2 3

## Confirmed EX/awakening key surface

The original game has real gameplay handlers for **Shift, B, Ctrl and Space**. They are not wrapper inventions. Most of these handlers use `Key.isDown(...)`, therefore the Android HUD should model them as held keys rather than very short one-shot pulses.

Key codes observed in AS2:

- Shift: `Key.isDown(16) || Key.isDown(53)`
- B: `Key.isDown(66)`
- Ctrl: `Key.isDown(17) || Key.isDown(54)`
- Space: `Key.isDown(32)`

## Spitfire / 스핏

Character animation-frame family: roughly `1..24`.

| Key | Original handler | Unlock / condition visible in script | Internal action evidence |
| --- | --- | --- | --- |
| Shift | DefineSprite_4088 | `스핏무기 == 3 || 소닉 == 1` | sets `케론 = 1`, character `gotoAndPlay(113)`, cooldown `신스킬4` |
| B | DefineSprite_4092 | `플라잉씨포 == 1` for visible button state | C4 branch uses `시포2`; alternate branch sets `플라잉 = 1` |
| Ctrl | DefineSprite_4103 | `스핏마스터 == 1` | consumes 3 cubes + 7 MP, sets `데인저 = 1`, cooldown `신스킬6` |
| Space | DefineSprite_4110 | `스핏2각기 == 1` | consumes 10 cubes + 30 MP, sets `슈퍼노바 = 1`, cooldown `신스킬7` |

## Ranger / 레인저

Character animation-frame family: roughly `29..63`.

| Key | Original handler | Unlock / condition visible in script | Internal action evidence |
| --- | --- | --- | --- |
| Shift | DefineSprite_4155 | `레인저무기 == 3 || 알피 == 1` | character `gotoAndPlay(47)`, action clip `gotoAndPlay(32)`, cooldown `신스킬4` |
| B | DefineSprite_4151 | handler present | consumes 2 cubes + 7 MP, sets `얼티밋 = 1`, cooldown `신스킬5` |
| Ctrl | DefineSprite_4165 | `레인저마스터 == 1` | consumes 3 cubes + 7 MP, sets `패드 = 1`, cooldown `신스킬6` |
| Space | DefineSprite_4172 | `레인저2각기 == 1` | consumes 10 cubes + 30 MP, sets `세븐즈 = 1`, cooldown `신스킬7` |

## Berserker / 버서커

Character animation-frame family: roughly `63..112`.

| Key | Original handler | Unlock / condition visible in script | Internal action evidence |
| --- | --- | --- | --- |
| Shift | DefineSprite_4213 | `블레이즈 == 3 || 멜티 == 1` | consumes 1 cube + 4 MP, character `gotoAndPlay(80)`, cooldown `신스킬5` |
| B | DefineSprite_4209 | `버스트퓨리 == 1` | consumes 2 cubes + 7 MP, sets `버스트 = 1`, cooldown `신스킬6` |
| Ctrl | DefineSprite_4221 | `버서커마스터 == 1` | consumes 3 cubes + 8 HP, sets `블붐 = 1`, cooldown `신스킬8` |
| Space | DefineSprite_4227 | `버서커2각기 == 1` | consumes 10 cubes + 30 MP, sets `리븐 = 1`, cooldown `신스킬7` |

## Weapon Master / 웨펀마스터

Character animation-frame family: roughly `100..143`.

| Key | Original handler | Unlock / condition visible in script | Internal action evidence |
| --- | --- | --- | --- |
| Shift | DefineSprite_4272 | `웨펀무기 == 5 || 울티 == 1` | consumes 5 MP, sets `차지버스트 = 1`, cooldown `신스킬1` |
| B | DefineSprite_4276 | `극초발도 == 1` | consumes 2 cubes + 6 MP, character `gotoAndPlay(143)`, cooldown `신스킬2` |
| Ctrl | DefineSprite_4283 | `웨펀마스터마스터 == 1` | consumes 3 cubes + 7 MP, sets `심검 = 1`, cooldown `신스킬6` |
| Space | DefineSprite_4288 | `웨펀2각기 == 1` and `일.이기._currentframe == 1` | consumes 10 cubes + 20 MP, sets `이검 = 1`, character `gotoAndPlay(129)` |

## Hidden professions

The SWF also contains Soul Bringer (`소울브링어`) and Launcher (`런처`). Launcher has a Space handler in the later character-frame family, while the four-key master/2nd-awakening pattern above is explicitly present for the four main professions. Do not assume every EX key exists for every hidden profession until the remaining handlers are traced.

## Android wrapper implications

v1.9 only exposed Shift + Space in `ControlLayoutConfig` and had no DOM `ControlLeft` mapping. B could pass through the generic A..Z mapper if invoked, but there was no touch target and B/Control were absent from the unconditional Ruffle key-release array.

v1.10 therefore:

- adds four class-neutral EX touch targets: Ctrl / Shift / Space / B;
- uses HOLD semantics for all four;
- maps Android Ctrl to browser `ControlLeft`;
- adds B and ControlLeft to unconditional DOM key-up recovery;
- keeps the v1.9 pointer ownership, skill paging, haptic feedback and press/ripple feedback unchanged.

## Visual-symbol tracing status

FFDec extraction currently yields:

- 2,596 button-state PNGs;
- 68 image assets;
- 1,407 filtered small-symbol candidates;
- 2,650 key-mapping hit blocks.

Sprite PNG export returns no usable files, but button/image export succeeds. Small image IDs `8893`, `8894`, `8895` and `1574` are visibly icon-like; they are **not yet assigned to a skill**. Do not ship them as a mapping until their SWF placement/dependency chain is proven.
