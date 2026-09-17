package com.aether.noema

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.State
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

private val Ink = Color(0xFF050507)
private val Ice = Color(0xFFC8F7FF)
private val Electric = Color(0xFF7B8CFF)
private val Violet = Color(0xFFC49BFF)
private val Silver = Color(0xFFE8E7E2)
private val Muted = Color(0xFF737C8F)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    background = Ink,
                    surface = Color(0xFF0B0C10),
                    primary = Ice,
                    secondary = Electric,
                    onBackground = Silver,
                    onSurface = Silver
                )
            ) { AetherRoot() }
        }
    }
}

@Composable
private fun AetherRoot() {
    var ready by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        delay(2920)
        ready = true
    }
    Crossfade(targetState = ready, animationSpec = tween(700), label = "scene") {
        if (it) Observatory() else Boot()
    }
}

@Composable
private fun Boot() {
    val p = remember { Animatable(0f) }
    LaunchedEffect(Unit) {
        p.animateTo(1f, tween(2680, easing = FastOutSlowInEasing))
    }

    Box(Modifier.fillMaxSize().background(Ink)) {
        Canvas(Modifier.fillMaxSize()) {
            val v = p.value
            val c = Offset(size.width / 2f, size.height * .46f)
            val short = min(size.width, size.height)

            drawRect(
                Brush.radialGradient(
                    listOf(Electric.copy(alpha = .13f * v), Color.Transparent),
                    c,
                    short * .72f
                )
            )

            for (i in 0 until 30) {
                val x = size.width * i / 29f
                val a = (.018f + .035f * sin(i * .73f + v * 5f).coerceAtLeast(0f)) * v
                drawLine(Ice.copy(alpha = a), Offset(x, size.height * .28f), Offset(x, size.height * .68f), .7f)
            }

            val beam = size.width * .66f * v
            drawLine(
                Brush.horizontalGradient(listOf(Color.Transparent, Ice.copy(.76f), Violet.copy(.58f), Color.Transparent)),
                Offset(c.x - beam / 2, c.y),
                Offset(c.x + beam / 2, c.y),
                1.25f
            )

            val base = 26f + short * .095f * v
            repeat(4) { i ->
                drawCircle(
                    listOf(Ice, Electric, Violet, Ice)[i].copy(alpha = (.24f - i * .035f) * v),
                    base + i * 17f,
                    c,
                    style = Stroke(if (i == 0) 1.5f else .85f)
                )
            }

            for (i in 0 until 72) {
                val a = i / 72f * PI.toFloat() * 2f
                val n = .5f + .5f * sin(i * 1.83f + v * 9f)
                val r1 = base + 48f
                val r2 = r1 + 4f + 18f * n
                drawLine(
                    Ice.copy(alpha = .035f + n * .1f * v),
                    Offset(c.x + cos(a) * r1, c.y + sin(a) * r1),
                    Offset(c.x + cos(a) * r2, c.y + sin(a) * r2),
                    .8f
                )
            }

            drawCircle(
                Brush.radialGradient(
                    listOf(Color.White.copy(.82f * v), Ice.copy(.28f * v), Electric.copy(.06f), Color.Transparent),
                    Offset(c.x - 9, c.y - 12),
                    54f
                ),
                54f,
                c,
                blendMode = BlendMode.Screen
            )
        }

        Column(
            Modifier.align(Alignment.Center).offset(y = 132.dp).alpha((p.value * 1.5f).coerceIn(0f, 1f)),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("A E T H E R", color = Silver, fontSize = 18.sp, fontWeight = FontWeight.Medium, letterSpacing = 5.sp)
            Spacer(Modifier.height(9.dp))
            Text(
                "SYNTHETIC OBSERVATORY / NODE 01",
                color = Muted, fontSize = 8.sp, letterSpacing = 2.sp, fontFamily = FontFamily.Monospace
            )
        }

        Row(
            Modifier.align(Alignment.BottomCenter).padding(bottom = 42.dp).fillMaxWidth(.64f),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(Modifier.weight(1f).height(1.dp).background(Color.White.copy(.08f))) {
                Box(
                    Modifier.fillMaxHeight().fillMaxWidth(p.value)
                        .background(Brush.horizontalGradient(listOf(Ice, Violet)))
                )
            }
            Spacer(Modifier.width(12.dp))
            Text(
                "${(p.value * 100).toInt().coerceAtMost(100).toString().padStart(3, '0')}%",
                color = Muted, fontSize = 8.sp, letterSpacing = 1.sp, fontFamily = FontFamily.Monospace
            )
        }
    }
}

@Composable
private fun Observatory() {
    val tilt by rememberTilt()
    val loop = rememberInfiniteTransition(label = "loop")
    val t by loop.animateFloat(
        0f, 1f,
        infiniteRepeatable(tween(14000, easing = LinearEasing)),
        label = "time"
    )
    val haptic = LocalHapticFeedback.current
    val scope = rememberCoroutineScope()
    val pulse = remember { Animatable(1f) }
    var mode by remember { mutableIntStateOf(0) }
    var serial by remember { mutableIntStateOf(27) }
    val names = listOf("FIELD", "TRACE", "VEIL")

    Box(Modifier.fillMaxSize().background(Ink)) {
        Ambient(t, tilt, mode, pulse.value)

        Column(
            Modifier.fillMaxSize().padding(horizontal = 22.dp, vertical = 22.dp)
        ) {
            Spacer(Modifier.height(20.dp))
            HeaderBand(t, names[mode])
            Spacer(Modifier.height(18.dp))

            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Metric("PHASE LOCK", String.format("%.4f", .9927 + sin(t * PI * 2).toFloat() * .0031f), Ice)
                Metric("SYNTHETIC BAND", String.format("%.2f THz", 12.42 + cos(t * PI * 4).toFloat() * .17f), Violet, true)
            }

            Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.offset(x = (tilt.x * 8f).dp, y = (tilt.y * 6f).dp)
                ) {
                    Box(
                        Modifier.size(294.dp).clip(CircleShape)
                            .clickable(
                                interactionSource = remember { MutableInteractionSource() },
                                indication = null
                            ) {
                                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                serial++
                                scope.launch {
                                    pulse.snapTo(0f)
                                    pulse.animateTo(1f, tween(1000, easing = FastOutSlowInEasing))
                                }
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Core(t, mode, pulse.value)
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                "Σ.${(serial % 100).toString().padStart(2, '0')}",
                                color = Silver, fontSize = 32.sp, fontWeight = FontWeight.Light, letterSpacing = 2.sp
                            )
                            Spacer(Modifier.height(7.dp))
                            Text(
                                "NOEMA CORE", color = Ice.copy(.62f), fontSize = 8.sp,
                                letterSpacing = 2.4.sp, fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                    Spacer(Modifier.height(7.dp))
                    Text(
                        "TOUCH TO COLLAPSE PHASE", color = Muted.copy(.76f), fontSize = 7.sp,
                        letterSpacing = 2.1.sp, fontFamily = FontFamily.Monospace
                    )
                }
            }

            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Bottom) {
                Metric("ENTROPY", String.format("%.5f", .03141 + sin(t * PI * 8).toFloat() * .004f), Electric)
                Column(horizontalAlignment = Alignment.End) {
                    Text("STATUS / COHERENT", color = Muted, fontSize = 7.sp, letterSpacing = 1.8.sp, fontFamily = FontFamily.Monospace)
                    Spacer(Modifier.height(5.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(5.dp).background(Ice, CircleShape))
                        Spacer(Modifier.width(7.dp))
                        Text("SYNCHRONIZED", color = Silver.copy(.88f), fontSize = 9.sp, letterSpacing = 1.4.sp, fontFamily = FontFamily.Monospace)
                    }
                }
            }

            Spacer(Modifier.height(24.dp))
            Dock(mode, names) {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                mode = it
            }
            Spacer(Modifier.height(10.dp))
        }
    }
}

@Composable
private fun HeaderBand(t: Float, mode: String) {
    Surface(
        color = Color(0xFF0B0D12).copy(.54f),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, Color.White.copy(.075f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(Modifier.padding(horizontal = 14.dp, vertical = 11.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(7.dp).background(Ice.copy(.92f), CircleShape))
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text("AETHER / $mode", color = Silver, fontSize = 9.sp, letterSpacing = 1.9.sp, fontWeight = FontWeight.SemiBold)
                Text("LOCAL SYNTHETIC OBSERVATORY", color = Muted, fontSize = 6.5.sp, letterSpacing = 1.5.sp, fontFamily = FontFamily.Monospace)
            }
            Text(
                "${(72 + 8 * sin(t * PI * 2).toFloat()).toInt()} fps",
                color = Ice.copy(.67f), fontSize = 7.sp, letterSpacing = 1.4.sp, fontFamily = FontFamily.Monospace
            )
        }
    }
}

@Composable
private fun Metric(label: String, value: String, accent: Color, end: Boolean = false) {
    Column(horizontalAlignment = if (end) Alignment.End else Alignment.Start) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (!end) {
                Box(Modifier.width(12.dp).height(1.dp).background(accent.copy(.7f)))
                Spacer(Modifier.width(7.dp))
            }
            Text(label, color = Muted, fontSize = 6.5.sp, letterSpacing = 1.7.sp, fontFamily = FontFamily.Monospace)
            if (end) {
                Spacer(Modifier.width(7.dp))
                Box(Modifier.width(12.dp).height(1.dp).background(accent.copy(.7f)))
            }
        }
        Spacer(Modifier.height(5.dp))
        Text(value, color = Silver, fontSize = 14.sp, fontWeight = FontWeight.Light, fontFamily = FontFamily.Monospace)
    }
}

@Composable
private fun Dock(selected: Int, names: List<String>, select: (Int) -> Unit) {
    Surface(
        color = Color(0xFF090B0F).copy(.78f),
        shape = RoundedCornerShape(22.dp),
        border = BorderStroke(1.dp, Color.White.copy(.07f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(Modifier.padding(5.dp), horizontalArrangement = Arrangement.spacedBy(5.dp)) {
            names.forEachIndexed { i, name ->
                val active = i == selected
                Box(
                    Modifier.weight(1f).clip(RoundedCornerShape(17.dp))
                        .background(
                            if (active) Brush.horizontalGradient(listOf(Ice.copy(.11f), Electric.copy(.16f), Violet.copy(.09f)))
                            else Brush.horizontalGradient(listOf(Color.Transparent, Color.Transparent))
                        )
                        .clickable { select(i) }
                        .padding(vertical = 12.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        name, color = if (active) Silver else Muted, fontSize = 8.sp, letterSpacing = 1.9.sp,
                        fontFamily = FontFamily.Monospace, fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal
                    )
                }
            }
        }
    }
}

@Composable
private fun Ambient(t: Float, tilt: Offset, mode: Int, pulse: Float) {
    Canvas(Modifier.fillMaxSize()) {
        val c = Offset(size.width * (.5f + tilt.x * .018f), size.height * (.45f + tilt.y * .012f))
        val short = min(size.width, size.height)
        val palette = if (mode == 2) listOf(Violet, Color(0xFF637FE0), Silver) else listOf(Ice, Electric, Violet)

        drawRect(Brush.verticalGradient(listOf(Color(0xFF07080B), Ink, Color(0xFF040406))))

        drawCircle(
            Brush.radialGradient(listOf(palette[1].copy(.12f), Color.Transparent), Offset(c.x + size.width * .2f, c.y - size.height * .12f), short * .86f),
            short * .86f, Offset(c.x + size.width * .2f, c.y - size.height * .12f)
        )
        drawCircle(
            Brush.radialGradient(listOf(palette[0].copy(.075f), Color.Transparent), Offset(c.x - size.width * .26f, c.y + size.height * .18f), short * .72f),
            short * .72f, Offset(c.x - size.width * .26f, c.y + size.height * .18f)
        )

        for (i in 0 until 80) {
            val seed = i * 12.9898f
            val px = ((sin(seed) * 43758.5453f) % 1f + 1f) % 1f
            val py = ((cos(seed * 1.77f) * 24634.6345f) % 1f + 1f) % 1f
            val drift = sin(t * PI.toFloat() * 2f + i * .37f) * 3f
            drawCircle(
                palette[i % 3].copy(alpha = .05f + (i % 5) * .012f),
                if (i % 9 == 0) 1.2f else .65f,
                Offset(px * size.width + tilt.x * (i % 7) * .65f, py * size.height + drift)
            )
        }

        for (i in 0 until 5) {
            val y = size.height * .72f + i * 7f
            val w = sin(t * PI.toFloat() * 2f + i * .8f) * 9f
            drawLine(
                Brush.horizontalGradient(listOf(Color.Transparent, palette[i % 3].copy(.075f), Color.Transparent)),
                Offset(0f, y + w), Offset(size.width, y - w), .7f
            )
        }

        if (pulse < 1f) {
            drawCircle(
                Ice.copy(alpha = (1f - pulse) * .22f),
                short * (.18f + pulse * .72f),
                c,
                style = Stroke(1.4f)
            )
        }
    }
}

@Composable
private fun Core(t: Float, mode: Int, pulse: Float) {
    Canvas(Modifier.fillMaxSize()) {
        val c = center
        val r = size.minDimension * .31f
        val rot = t * 360f
        val palette = if (mode == 2) listOf(Violet, Color(0xFF85A0FF), Silver) else listOf(Ice, Electric, Violet)

        drawCircle(
            Brush.radialGradient(
                listOf(Color.White.copy(.12f), palette[0].copy(.09f), palette[1].copy(.035f), Color.Transparent),
                Offset(c.x - r * .24f, c.y - r * .29f), r * 2f
            ),
            r * 1.85f, c
        )

        repeat(3) { i ->
            drawCircle(palette[i].copy(alpha = .13f - i * .018f), r * (.98f + i * .29f), c, style = Stroke(if (i == 0) 1.4f else .85f))
        }

        val rect = Rect(c.x - r * 1.34f, c.y - r * 1.34f, c.x + r * 1.34f, c.y + r * 1.34f)
        drawArc(Ice.copy(.72f), rot, 47f, false, rect.topLeft, rect.size, style = Stroke(2.2f, cap = StrokeCap.Round))
        drawArc(
            Violet.copy(.42f), -rot * .73f + 126f, 83f, false,
            Offset(c.x - r * 1.58f, c.y - r * 1.58f), Size(r * 3.16f, r * 3.16f),
            style = Stroke(1.15f, cap = StrokeCap.Round)
        )

        for (i in 0 until 96) {
            val a = i / 96f * PI.toFloat() * 2f
            val w = .45f + .55f * sin(i * 1.71f + t * PI.toFloat() * 8f)
            val r1 = r * 1.55f
            val r2 = r1 + 3f + w * 14f
            drawLine(
                palette[i % 3].copy(alpha = .028f + w * .09f),
                Offset(c.x + cos(a) * r1, c.y + sin(a) * r1),
                Offset(c.x + cos(a) * r2, c.y + sin(a) * r2),
                if (i % 12 == 0) 1.1f else .65f
            )
        }

        for (i in 0 until 7) {
            val a = t * PI.toFloat() * 2f * if (i % 2 == 0) 1f else -.68f + i * .91f
            val rr = r * (1.05f + (i % 3) * .22f)
            val pt = Offset(c.x + cos(a) * rr, c.y + sin(a) * rr)
            drawCircle(
                Brush.radialGradient(listOf(palette[i % 3].copy(.95f), Color.Transparent), pt, 10f),
                10f, pt, blendMode = BlendMode.Screen
            )
            drawCircle(palette[i % 3].copy(.92f), 1.5f, pt)
        }

        drawCircle(
            Brush.radialGradient(
                listOf(Color.White.copy(.56f), Ice.copy(.15f), Electric.copy(.05f), Color.Transparent),
                Offset(c.x - r * .18f, c.y - r * .22f), r * .88f
            ),
            r * .86f, c, blendMode = BlendMode.Screen
        )

        if (pulse < 1f) {
            drawCircle(Color.White.copy(alpha = (1f - pulse) * .42f), r * (.72f + pulse * 1.2f), c, style = Stroke(2f))
        }
    }
}

@Composable
private fun rememberTilt(): State<Offset> {
    val context = LocalContext.current
    val state = remember { mutableStateOf(Offset.Zero) }

    DisposableEffect(context) {
        val manager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val sensor = manager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val listener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent) {
                state.value = Offset(
                    (-event.values[0] / SensorManager.GRAVITY_EARTH).coerceIn(-1f, 1f),
                    (event.values[1] / SensorManager.GRAVITY_EARTH).coerceIn(-1f, 1f)
                )
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit
        }
        if (sensor != null) manager.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_GAME)
        onDispose { manager.unregisterListener(listener) }
    }
    return state
}
