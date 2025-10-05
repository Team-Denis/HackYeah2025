package com.example.denisplanner.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = Purple80,
    secondary = PurpleGrey80,
    tertiary = Pink80
)

val shadcnPrimary = Color(0xFF0F172A)       // Slate-900 (deep, sophisticated)
val shadcnSecondary = Color(0xFF475569)     // Slate-600 (balanced gray)
val shadcnTertiary = Color(0xFF64748B)      // Slate-500 (lighter gray accent)

val shadcnBackground = Color(0xFFFAFAFA)    // Slate-50 (very light, warm white)
val shadcnSurface = Color(0xFFFFFFFF)       // Pure white
val shadcnOnPrimary = Color(0xFFFFFFFF)     // White text on primary
val shadcnOnSecondary = Color(0xFFFFFFFF)   // White text on secondary
val shadcnOnTertiary = Color(0xFFFFFFFF)    // White text on tertiary
val shadcnOnBackground = Color(0xFF0F172A)  // Slate-900 (dark text)
val shadcnOnSurface = Color(0xFF1E293B)     // Slate-800 (slightly softer dark text)

private val LightColorScheme = lightColorScheme(
    primary = shadcnPrimary,
    secondary = shadcnSecondary,
    tertiary = shadcnTertiary,
    background = shadcnBackground,
    surface = shadcnSurface,
    onPrimary = shadcnOnPrimary,
    onSecondary = shadcnOnSecondary,
    onTertiary = shadcnOnTertiary,
    onBackground = shadcnOnBackground,
    onSurface = shadcnOnSurface,
)

//private val LightColorScheme = lightColorScheme(
//    primary = Color(0xFF0D99FF),        // Bright blue - great for primary accents
//    secondary = Color(0xFF00C49A),      // Teal green - nice contrast to blue
//    tertiary = Color(0xFFFF6F61),       // Coral red - vibrant but not too loud
//
//    background = Color(0xFFF8FAFB),     // Very light gray-blue, soft background
//    surface = Color(0xFFFFFFFF),        // Pure white surface
//    onPrimary = Color.White,             // Text/icons on primary color
//    onSecondary = Color.White,
//    onTertiary = Color.White,
//    onBackground = Color(0xFF1C1C1E),   // Dark gray for text on background
//    onSurface = Color(0xFF1C1C1E)
//)

//private val LightColorScheme = lightColorScheme(
//    primary = Purple40,
//    secondary = PurpleGrey40,
//    tertiary = Pink40
//
//    /* Other default colors to override
//    background = Color(0xFFFFFBFE),
//    surface = Color(0xFFFFFBFE),
//    onPrimary = Color.White,
//    onSecondary = Color.White,
//    onTertiary = Color.White,
//    onBackground = Color(0xFF1C1B1F),
//    onSurface = Color(0xFF1C1B1F),
//    */
//)

@Composable
fun DenisPlannerTheme(
    darkTheme: Boolean = false,
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }

        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}