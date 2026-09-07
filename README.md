# 雷巴的冒险 Android 高保真运行壳 v1.1

目标：**尽量直接运行《雷巴的冒险 / 勇闯地下城3.0 Final》的原 Flash 核心，而不是重写玩法。**

本仓库默认**不夹带游戏本体**。App 会在用户主动选择后获取公开保存源，或导入用户已有 SWF / FINAL.exe / Final.zip；验证通过后将本体保存在应用私有目录，再由内置 Ruffle self-hosted 播放。

## 当前运行路径

### 1. 本地原 SWF + Ruffle（主路径）

启动时如果应用私有目录已经存在合法 `game.swf`，直接进入：

`https://reva.local/player.html` → 内置 Ruffle → `https://reva.local/game.swf`

`reva.local` 不是联网服务器，而是 Android WebView 内部拦截的虚拟 HTTPS Origin。HTML / JS / WASM / SWF 都按正确 MIME 返回，避免 `file://` 下 WASM、CORS 和 Origin 的兼容问题。

### 2. 智能获取原版本体：4399 → 韩国 Final → 官方 Final.zip

左上角 `⋮` → **智能获取本体**，按顺序尝试：

1. **4399 游戏 234798 实时解析**：游戏页 → 播放页 → server JS → `webServer + _strGamePath` → 探测真实 SWF。
2. **韩国保存的 Final 单 SWF**：Google Drive ID `1iNaM6v8hvgJJcHXxL2TcNf12eubqgRDJ`。
3. **历史官方 reva.kr Final.zip**：Drive ID `0B4rnLgqFctGvbXpYbVN0ZHliN0E`；下载 ZIP 后自动找到 Final EXE，并按 Windows Flash Projector footer 提取内嵌 SWF。
4. 三条在线路径都失败时，可直接 **导入 SWF / FINAL.exe / Final.zip**。App 按文件内容魔数识别，不依赖扩展名：SWF 直接校验；经典 Windows Flash Projector EXE 自动抽内嵌 SWF；ZIP 自动寻找 Final EXE 后再抽 SWF。

获取后的 SWF 必须：

- 以 `FWS` / `CWS` / `ZWS` 开头；
- 实际文件不小于 30 MiB；
- 可读出 SWF version 和 declared uncompressed length；
- 自动计算 SHA-256；
- 来源、大小、版本、SHA 会写入应用私有 `game_source.txt`。

### 3. 4399 H5 在线备用

菜单仍保留 4399 HTML5 页作为网络备用路线。它不是高保真首选；本地原 SWF + Ruffle 才是主目标。

## 触控映射

原版键位尽量原样映射，不改成现代手游自动连招：

- 左侧：`←` / `↓`（后跳）/ `→`
- 常驻：`X` 攻击、`C` 跳跃、`Z`、`V` 抓取
- 技能组三档：`ASDF` / `GHQW` / `ERTY`
- 辅助：`Shift` / `Space` / `1` / `2` / `3`

触控层按 Android `pointerId` 路由，多指可以同时保持方向 + 攻击/技能。没有落在按钮上的触摸会透传给 WebView，因此角色选择、商店、菜单等原游戏点击区域不会被透明触控层吞掉。

## Ruffle

CI 会下载固定版本的 Ruffle self-hosted Web 包并直接打入 APK assets：

`nightly-2026-09-05`

APK 运行原 SWF 时不依赖 Ruffle CDN。

### 4. 万能本体导入（v1.1）

左上角 `⋮` → **导入 SWF / FINAL.exe / Final.zip**。文件名可以被浏览器改掉，App 按内容识别：

- `FWS / CWS / ZWS` → 原 SWF；
- `MZ` → 经典 Windows Flash Projector EXE，读取 footer 并抽出内嵌 SWF；
- `PK` → ZIP，自动寻找最可能的 Final EXE，再抽出 SWF。

转换完成后仍走同一套安全安装流程：SWF 头校验、最低 Final 体积校验、写入后复检、SHA-256、旧本体备份/失败回滚。

## GitHub Actions（推荐）

仓库已包含 `.github/workflows/build-apk.yml`。推到 GitHub 后，`main/master` push 或手动 `workflow_dispatch` 会：

1. 安装 Android 35 SDK / Build Tools 35.0.0；
2. 下载并内置固定 Ruffle；
3. 运行本地核心 QA；
4. `assembleDebug` 生成 APK；
5. 用 `aapt` 验 package / targetSdk / Ruffle assets；
6. 启动 API 35 Android 模拟器；
7. 安装 APK，先启动 `qa_ruffle.html`，让 **APK 内置的 Ruffle JS/WASM 真正加载一个合法 FWS 测试片**，必须出现 `RUFFLE_QA_READY`；
8. 启动内部输入测试页，**真实点击原生 X 触控按钮，检查 WebView 收到 X keydown / keyup**；
9. 正常启动 App、后台/恢复，检查崩溃 / ANR；
10. 上传 APK、SHA-256、badging、Ruffle/输入链 logcat 和模拟器截图。

产物名：`reva-android-debug`。

### Android Studio

也可以直接用 Android Studio 打开根目录并构建 `app`。要求 Android SDK 35。

## 本地 QA

当前不依赖 Android SDK 的核心逻辑可以直接运行：

```bash
bash qa/run_local_qa.sh
```

它会真实用 `javac` 编译并执行：

- 4399 解析器 fixture；
- Google Drive 大文件确认页解析；
- `FWS/CWS/ZWS` 文件头检查；
- 坏 SWF 拒绝；
- Windows Flash Projector EXE → SWF 提取；
- Final.zip → EXE → SWF 提取。

## 桌面工具

校验已有 SWF：

```bash
python tools/verify_swf.py path/to/game.swf
```

从 Windows Flash Projector EXE 提取 SWF：

```bash
python tools/extract_projector.py '雷巴的冒险 FINAL.exe' extracted.swf
```

从官方 Final.zip 自动找到 EXE 并提取：

```bash
python tools/extract_official_final.py FINAL.zip extracted.swf
```

比较两个发行版：

```bash
python tools/compare_swf.py 4399.swf korean_final.swf
```

这会比较签名、SWF version、实际大小、声明解压大小、SHA-256，并明确报告是否逐字节相同。

## 已验证与尚未验证

详见 [`STATUS.md`](STATUS.md)。最重要的区分是：

- **纯 Java/工程 QA 已在当前环境真实执行并通过。**
- **GitHub Actions 的 Android 模拟器链已完整写好，且 GitHub 账户连接已可读；但当前连接账户还没有可用仓库，连接器也不提供“创建仓库”动作，因此 workflow 尚未实际触发。APK/模拟器结果不能冒充已经 PASS。**
- **原 Final SWF 没有被打包进本项目。** 当前环境的外部二进制下载受限，因此原版二进制的真机 Ruffle 兼容结果仍需要获得本体后验证。

## 工程定位

这是一个“原版保存/兼容运行壳”：优先保留原游戏逻辑、动画、AI、关卡和手感，再解决 Android 的触控、WebView、Ruffle 和打包问题。Godot 原生复刻工程可以继续作为后续备用路线，但不替代这条原版核心路线。
