#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
main = root / 'app/src/main/java/com/ajiu/reva/MainActivity.java'
gradle = root / 'app/build.gradle'
html = root / 'app/src/main/assets/index.html'

s = main.read_text()
needle = '    WebResourceResponse interceptLocal(Uri uri) {\n'
if needle not in s:
    raise SystemExit('interceptLocal insertion point not found')
insert = needle + '''        // Reva 3.0 EX keeps several resources outside the main SWF.\n        // Serve those files from APK assets through the same virtual HTTPS origin so\n        // AS2 loadMovie/loadSound resolve exactly as they did beside the original SWF.\n        if(uri != null && "reva.local".equalsIgnoreCase(uri.getHost())) {\n            String pth = uri.getPath();\n            if(pth != null && pth.startsWith("/BGM/") && !pth.contains("..")) {\n                String assetPath = pth.substring(1);\n                try {\n                    String lower = assetPath.toLowerCase(Locale.US);\n                    String mime = lower.endsWith(".mp3") ? "audio/mpeg" :\n                                  (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) ? "image/jpeg" :\n                                  lower.endsWith(".png") ? "image/png" : "application/octet-stream";\n                    InputStream in = getAssets().open(assetPath);\n                    android.util.Log.i("REVA_ASSET", "SERVE:" + assetPath);\n                    return new WebResourceResponse(mime, null, in);\n                } catch(Exception e) {\n                    android.util.Log.e("REVA_ASSET", "MISS:" + assetPath + ":" + e.getClass().getSimpleName());\n                }\n            }\n        }\n'''
s = s.replace(needle, insert, 1)
main.write_text(s)

g = gradle.read_text()
if 'versionCode 16' not in g or "versionName '1.6'" not in g:
    raise SystemExit('expected v1.6 version markers not found')
g = g.replace('versionCode 16', 'versionCode 17', 1).replace("versionName '1.6'", "versionName '1.7'", 1)
gradle.write_text(g)

h = html.read_text()
h = h.replace('正在载入 Final SWF…', '正在载入 3.0 EX 汉化本体…')
h = h.replace('Ruffle 与 3.0 EX 汉化本体均随 APK 内置；正常启动完全离线。',
              'Ruffle、3.0 EX 汉化本体及其外部 BGM 资源均随 APK 内置；正常启动完全离线。')
html.write_text(h)

print('PASS apply_v17: EX BGM virtual-origin routing + v1.7 metadata')
