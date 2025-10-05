package com.example.denisplanner

import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.graphics.createBitmap
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.denisplanner.viewmodel.MapViewModel
import com.example.denisplanner.viewmodel.MapViewState
import com.example.denisplanner.service.MapboxSearchService
import com.example.denisplanner.service.Itinerary
import com.example.denisplanner.service.Suggestion
import com.example.denisplanner.ui.theme.DenisPlannerTheme
import com.example.denisplanner.utils.RequestLocationPermission
import com.mapbox.bindgen.DataRef
import com.mapbox.geojson.Point
import com.mapbox.geojson.LineString
import com.mapbox.maps.extension.compose.MapboxMap
import com.mapbox.maps.extension.compose.animation.viewport.rememberMapViewportState
import com.mapbox.maps.extension.compose.animation.viewport.MapViewportState
import com.mapbox.maps.extension.compose.style.MapStyle
import com.mapbox.maps.extension.compose.MapEffect
import com.mapbox.maps.extension.compose.DisposableMapEffect
import com.mapbox.maps.extension.compose.annotation.generated.PolylineAnnotation
import com.mapbox.maps.extension.compose.annotation.generated.CircleAnnotation
import com.mapbox.maps.extension.style.layers.addLayer
import com.mapbox.maps.extension.style.layers.addLayerBelow
import com.mapbox.maps.extension.style.layers.generated.lineLayer
import com.mapbox.maps.extension.style.layers.properties.generated.ProjectionName
import com.mapbox.maps.extension.style.projection.generated.Projection
import com.mapbox.maps.extension.style.projection.generated.setProjection
import com.mapbox.maps.extension.style.sources.addSource
import com.mapbox.maps.extension.style.sources.generated.geoJsonSource
import com.mapbox.maps.plugin.PuckBearing
import com.mapbox.maps.plugin.locationcomponent.createDefault2DPuck
import com.mapbox.maps.plugin.locationcomponent.location
import com.mapbox.maps.plugin.viewport.ViewportStatus
import com.mapbox.maps.plugin.gestures.gestures
import com.mapbox.maps.plugin.viewport.data.FollowPuckViewportStateOptions
import com.mapbox.maps.plugin.viewport.data.OverviewViewportStateOptions
import com.mapbox.maps.EdgeInsets
import kotlinx.coroutines.launch
import androidx.core.graphics.set
import com.mapbox.maps.extension.style.expressions.generated.Expression.Companion.interpolate
import com.mapbox.maps.extension.style.layers.properties.generated.LineJoin
import com.mapbox.maps.plugin.locationcomponent.OnIndicatorPositionChangedListener
import com.example.denisplanner.location.SimulateRouteLocationProvider
import com.example.denisplanner.service.TripPOI
import com.mapbox.maps.plugin.locationcomponent.DefaultLocationProvider
import com.mapbox.maps.plugin.locationcomponent.LocationProvider


const val WALKING_DOTS_IMAGE_ID = "walking-dots"
const val ROUTE_LAYER_ID = "route-layer"
const val ROUTE_SOURCE_ID = "route-source"
const val LINE_BASE_WIDTH = 7.0

// Route segment data class for different transportation modes
data class RouteSegment(
    val mode: String,
    val points: List<Point>,
    val routeInfo: String?
)

// Transportation mode layer IDs
const val WALK_LAYER_ID = "walk-layer"
const val WALK_SOURCE_ID = "walk-source"
const val TRANSIT_LAYER_ID = "transit-layer"
const val TRANSIT_SOURCE_ID = "transit-source"
const val BUS_LAYER_ID = "bus-layer"
const val BUS_SOURCE_ID = "bus-source"
const val TRAM_LAYER_ID = "tram-layer"
const val TRAM_SOURCE_ID = "tram-source"
const val SUBWAY_LAYER_ID = "subway-layer"
const val SUBWAY_SOURCE_ID = "subway-source"

// Transportation mode colors
val WALK_COLOR = Color(0xFF64748B)     // Slate-500 for walking
val TRANSIT_COLOR = Color(0xFF2563EB)  // Blue-600 for general transit
val BUS_COLOR = Color(0xFF16A34A)      // Green-600 for bus
val TRAM_COLOR = Color(0xFFEA580C)     // Orange-600 for tram
val SUBWAY_COLOR = Color(0xFF7C3AED)   // Purple-600 for subway

// Helper data class for transportation mode configuration
data class TransportModeConfig(
    val sourceId: String,
    val layerId: String, 
    val color: Color,
    val shouldUseDots: Boolean
)

fun createWalkingDotsImage(): com.mapbox.maps.Image {
    val size = 64
    val bitmap = createBitmap(size, size)

    // Fill bitmap with transparent background
    for (x in 0 until size) {
        for (y in 0 until size) {
            bitmap[x, y] = android.graphics.Color.TRANSPARENT
        }
    }

    // Draw circle in center
    val centerX = size / 2f
    val centerY = size / 2f
    val radius = 8.0 * 2 // Size of the dot

    for (x in 0 until size) {
        for (y in 0 until size) {
            val dx = x - centerX
            val dy = y - centerY
            val distance = kotlin.math.sqrt(dx * dx + dy * dy)

            if (distance <= radius) {
                bitmap[x, y] = android.graphics.Color.argb(255, 25, 118, 210)
            }
        }
    }

    val pixels = IntArray(size * size)
    bitmap.getPixels(pixels, 0, size, 0, 0, size, size)

    val imageData = ByteArray(size * size * 4)
    for (i in pixels.indices) {
        val pixel = pixels[i]
        val index = i * 4
        imageData[index] = (pixel shr 16 and 0xFF).toByte()
        imageData[index + 1] = (pixel shr 8 and 0xFF).toByte()
        imageData[index + 2] = (pixel and 0xFF).toByte()
        imageData[index + 3] = (pixel shr 24 and 0xFF).toByte()
    }

    val dataRef = DataRef.allocateNative(imageData.size)
    val byteBuffer = dataRef.buffer
    byteBuffer.put(imageData)
    byteBuffer.rewind()

    return com.mapbox.maps.Image(size, size, dataRef)
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            DenisPlannerTheme {
                MapScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MapScreen(
    viewModel: MapViewModel = viewModel()
) {
    BackHandler(enabled = viewModel.canGoBack) {
        viewModel.goBack()
    }

    val context = LocalContext.current
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    var permissionRequestCount by remember { mutableStateOf(1) }
    var showMap by remember { mutableStateOf(false) }
    var showRequestPermissionButton by remember { mutableStateOf(false) }

    val currentState = viewModel.currentState
    val uiData = viewModel.uiData

    // Default location (Krakow) as fallback
    val defaultLocation = Point.fromLngLat(19.9450, 50.0647)

    val mapViewportState = rememberMapViewportState {
        setCameraOptions {
            zoom(14.0)
            center(defaultLocation)
            pitch(0.0)
            bearing(0.0)
        }
    }

    val bottomSheetState = rememberModalBottomSheetState(
        skipPartiallyExpanded = false
    )

    LaunchedEffect(uiData.errorMessage) {
        uiData.errorMessage?.let { message ->
            snackbarHostState.showSnackbar(message)
            viewModel.clearError()
        }
    }

    RequestLocationPermission(
        requestCount = permissionRequestCount,
        onPermissionDenied = {
            scope.launch {
                snackbarHostState.showSnackbar("You need to accept location permissions.")
            }
            showRequestPermissionButton = true
        },
        onPermissionReady = {
            showRequestPermissionButton = false
            showMap = true
        }
    )

    Box(modifier = Modifier.fillMaxSize()) {
        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier.align(Alignment.BottomCenter)
        )

        if (showMap) {
            MapboxMap(
                Modifier.fillMaxSize(),
                mapViewportState = mapViewportState,
                style = { MapStyle(style = "mapbox://styles/mapbox/navigation-day-v1") },
                scaleBar = {},
                compass = {},
                logo = {
                    Logo()
                },
                attribution = {
                    Attribution()
                }
            ) {
                MapEffect(Unit) { mapView ->
                    mapView.mapboxMap.loadStyle("mapbox://styles/mapbox/navigation-day-v1") { style ->
                        try {
                            val walkingDotsImage = createWalkingDotsImage()
                            style.addStyleImage(
                                WALKING_DOTS_IMAGE_ID,
                                image = walkingDotsImage,
                                sdf = false,
                                stretchX = emptyList(),
                                stretchY = emptyList(),
                                content = null,
                                scale = 1.0f
                            )
                        } catch (e: Exception) {
                            Log.w("MapStyle", "Failed to add walking dots pattern: ${e.message}")
                        }
                    }

                    mapView.mapboxMap.setProjection(
                        projection = Projection(ProjectionName.MERCATOR)
                    )

                    mapView.gestures.updateSettings {
                        pitchEnabled = false
                    }

                    mapViewportState.transitionToFollowPuckState(
                        followPuckViewportStateOptions = FollowPuckViewportStateOptions.Builder()
                            .pitch(0.0)
                            .build()
                    )
                }

                // Handle route simulation - extract route processing by transportation mode
                val routeSegments = remember(currentState) {
                    when (currentState) {
                        is MapViewState.RouteSelected, is MapViewState.Simulating -> {
                            val route = when (currentState) {
                                is MapViewState.RouteSelected -> currentState.selectedRoute
                                is MapViewState.Simulating -> currentState.selectedRoute
                                else -> null
                            }
                            route?.legs?.mapNotNull { leg ->
                                try {
                                    val points = decodePolyline(leg.legGeometry)
                                    if (points.isNotEmpty()) {
                                        RouteSegment(
                                            mode = leg.mode,
                                            points = points,
                                            routeInfo = leg.routeShortName ?: leg.routeLongName
                                        )
                                    } else null
                                } catch (e: Exception) {
                                    null
                                }
                            }?.takeIf { it.isNotEmpty() }
                        }
                        else -> null
                    }
                }
                
                // Calculate total route points for viewport overview
                val allRoutePoints = remember(routeSegments) {
                    routeSegments?.flatMap { it.points }
                }
                
                val routeLine = remember(allRoutePoints) {
                    allRoutePoints?.let { LineString.fromLngLats(it) }
                }
                
                MapEffect(routeLine, currentState) { mapView ->
                    if ((currentState is MapViewState.Simulating) && routeLine != null) {
                        val currentProvider = mapView.location.getLocationProvider()
                        if (currentProvider !is SimulateRouteLocationProvider) {
                            val simulateProvider = SimulateRouteLocationProvider(
                                route = routeLine,
                                startingLocation = viewModel.currentPuckLocation,
                                updateIntervalMs = 1000L
                            )
                            mapView.location.setLocationProvider(simulateProvider)
                            mapView.location.enabled = true
                        }

                        mapViewportState.transitionToFollowPuckState(
                            followPuckViewportStateOptions = FollowPuckViewportStateOptions.Builder()
                                .pitch(0.0)
                                .build()
                        )
                    } else if (currentState !is MapViewState.DelayReporting) {
                        mapView.location.setLocationProvider(DefaultLocationProvider(context))
                        mapView.location.enabled = true
                    }
                }
                
                DisposableMapEffect(Unit) { mapView ->
                    mapView.location.updateSettings {
                        locationPuck = createDefault2DPuck(withBearing = false)
                        puckBearingEnabled = false
                        pulsingEnabled = true
                        enabled = true
                    }

                    val positionListener = OnIndicatorPositionChangedListener { point ->
                        viewModel.updatePuckLocation(point)
                    }
                    mapView.location.addOnIndicatorPositionChangedListener(positionListener)
                    
                    onDispose {
                        mapView.location.removeOnIndicatorPositionChangedListener(positionListener)
                    }
                }


                // Route rendering with separate layers for each transportation mode
                MapEffect(routeSegments) { mapView ->
                    val mapboxMap = mapView.mapboxMap

                    // Remove old route layers/sources if they exist
                    mapboxMap.style?.apply {
                        // Clean up old single-layer approach
                        if (styleLayerExists(ROUTE_LAYER_ID)) {
                            removeStyleLayer(ROUTE_LAYER_ID)
                        }
                        if (styleSourceExists(ROUTE_SOURCE_ID)) {
                            removeStyleSource(ROUTE_SOURCE_ID)
                        }
                        
                        // Clean up all transportation mode layers
                        listOf(WALK_LAYER_ID, TRANSIT_LAYER_ID, BUS_LAYER_ID, TRAM_LAYER_ID, SUBWAY_LAYER_ID).forEach { layerId ->
                            if (styleLayerExists(layerId)) {
                                removeStyleLayer(layerId)
                            }
                        }
                        listOf(WALK_SOURCE_ID, TRANSIT_SOURCE_ID, BUS_SOURCE_ID, TRAM_SOURCE_ID, SUBWAY_SOURCE_ID).forEach { sourceId ->
                            if (styleSourceExists(sourceId)) {
                                removeStyleSource(sourceId)
                            }
                        }
                    }

                    routeSegments?.let { segments ->
                        if (segments.isNotEmpty()) {
                            // Switch to overview mode to show full route (except during simulation)
                            if (currentState !is MapViewState.Simulating && allRoutePoints?.isNotEmpty() == true) {
                                val lineString = LineString.fromLngLats(allRoutePoints)
                                mapViewportState.transitionToOverviewState(
                                    overviewViewportStateOptions = OverviewViewportStateOptions.Builder()
                                        .geometry(lineString)
                                        .padding(EdgeInsets(50.0, 50.0, 50.0, 50.0))
                                        .build()
                                )
                            }

                            mapboxMap.style?.apply {
                                // Group segments by transportation mode
                                val groupedSegments = segments.groupBy { segment ->
                                    when (segment.mode.uppercase()) {
                                        "WALK" -> "WALK"
                                        "BUS" -> "BUS"
                                        "TRAM" -> "TRAM"
                                        "SUBWAY", "RAIL" -> "SUBWAY"
                                        else -> "TRANSIT"
                                    }
                                }

                                // Create layers for each transportation mode found
                                groupedSegments.forEach { (mode, modeSegments) ->
                                    val allModePoints = modeSegments.flatMap { it.points }
                                    if (allModePoints.isNotEmpty()) {
                                        val lineString = LineString.fromLngLats(allModePoints)
                                        
                                        val config = when (mode) {
                                            "WALK" -> TransportModeConfig(WALK_SOURCE_ID, WALK_LAYER_ID, WALK_COLOR, true)
                                            "BUS" -> TransportModeConfig(BUS_SOURCE_ID, BUS_LAYER_ID, BUS_COLOR, false)
                                            "TRAM" -> TransportModeConfig(TRAM_SOURCE_ID, TRAM_LAYER_ID, TRAM_COLOR, false)
                                            "SUBWAY" -> TransportModeConfig(SUBWAY_SOURCE_ID, SUBWAY_LAYER_ID, SUBWAY_COLOR, false)
                                            else -> TransportModeConfig(TRANSIT_SOURCE_ID, TRANSIT_LAYER_ID, TRANSIT_COLOR, false)
                                        }

                                        addSource(geoJsonSource(config.sourceId) {
                                            geometry(lineString)
                                            lineMetrics(true)
                                        })

                                        val layerConfig = lineLayer(config.layerId, config.sourceId) {
                                            lineJoin(LineJoin.ROUND)
                                            lineWidth(
                                                interpolate {
                                                    exponential(1.5)
                                                    zoom()
                                                    stop(10.0, if (config.shouldUseDots) LINE_BASE_WIDTH * 0.8 else LINE_BASE_WIDTH)
                                                    stop(14.0, if (config.shouldUseDots) LINE_BASE_WIDTH * 1.2 else LINE_BASE_WIDTH * 1.5)
                                                    stop(18.0, if (config.shouldUseDots) LINE_BASE_WIDTH * 1.6 else LINE_BASE_WIDTH * 2.0)
                                                }
                                            )
                                            if (config.shouldUseDots) {
                                                linePattern(WALKING_DOTS_IMAGE_ID)
                                            } else {
                                                lineColor(config.color.toArgb())
                                                lineCap(com.mapbox.maps.extension.style.layers.properties.generated.LineCap.ROUND)
                                            }
                                        }

                                        addLayerBelow(layerConfig, below = "mapbox-location-indicator-layer")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Show locate button when viewport is in Idle state
        if (showMap && mapViewportState.mapViewportStatus == ViewportStatus.Idle) {
            FloatingActionButton(
                onClick = {
                    mapViewportState.transitionToFollowPuckState(
                        followPuckViewportStateOptions = FollowPuckViewportStateOptions.Builder()
                            .pitch(0.0)
                            .build()
                    )
                },
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(bottom = 190.dp, end = 16.dp),
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.surface,
            ) {
                Icon(
                    imageVector = Icons.Default.MyLocation,
                    contentDescription = "Locate button"
                )
            }
        }
        

        // Permission request buttons
        if (showRequestPermissionButton) {
            Column(modifier = Modifier.align(Alignment.Center)) {
                Button(
                    modifier = Modifier.align(Alignment.CenterHorizontally),
                    onClick = {
                        permissionRequestCount += 1
                    }
                ) {
                    Text("Request permission again ($permissionRequestCount)")
                }
                Button(
                    modifier = Modifier.align(Alignment.CenterHorizontally),
                    onClick = {
                        context.startActivity(
                            Intent(
                                android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                Uri.fromParts("package", context.packageName, null)
                            )
                        )
                    }
                ) {
                    Text("Show App Settings page")
                }
            }
        }

        // Compact search bar that triggers bottom sheet (show in home and search states)
        val shouldShowSearchBar = showMap && when (currentState) {
            is MapViewState.Home -> true // Always show in home state
            is MapViewState.SearchingLocation -> true // Show with bottom sheet
            is MapViewState.RouteOverview -> false // Hide during route overview
            is MapViewState.RouteSelected -> false // Hide during route selection
            is MapViewState.Simulating -> false // Hide during simulation
            is MapViewState.DelayReporting -> false
        }
        
        if (shouldShowSearchBar) {
            SearchBarTrigger(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 90.dp, start = 16.dp, end = 16.dp),
                onClick = { viewModel.showBottomSheet() },
                isLoading = false
            )
        }

        // Bottom sheet with full search functionality
        if ((currentState is MapViewState.Home && currentState.showBottomSheet) || currentState is MapViewState.SearchingLocation) {
            ModalBottomSheet(
                onDismissRequest = { viewModel.hideBottomSheet() },
                sheetState = bottomSheetState,
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface,
                dragHandle = {
                    Box(
                        modifier = Modifier
                            .padding(vertical = 12.dp)
                            .width(32.dp)
                            .height(4.dp)
                            .background(
                                MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f),
                                RoundedCornerShape(2.dp)
                            )
                    )
                }
            ) {
                SearchBottomSheetContent(
                    mapViewportState = mapViewportState,
                    onLocationSelected = { suggestion, searchService ->
                        viewModel.selectLocation(suggestion, searchService)
                    },
                    onDismiss = { viewModel.hideBottomSheet() }
                )
            }
        }
        
        // Routes bottom sheet
        if (currentState is MapViewState.RouteOverview) {
            ModalBottomSheet(
                onDismissRequest = { viewModel.goToHome() },
                sheetState = bottomSheetState,
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface,
                dragHandle = {
                    Box(
                        modifier = Modifier
                            .padding(vertical = 12.dp)
                            .width(32.dp)
                            .height(4.dp)
                            .background(
                                MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f),
                                RoundedCornerShape(2.dp)
                            )
                    )
                }
            ) {
                RoutesBottomSheetContent(
                    routes = currentState.routes,
                    destination = currentState.currentLocation.name,
                    onRouteSelected = { route ->
                        viewModel.selectRoute(route)
                    },
                    onDismiss = { viewModel.goToHome() }
                )
            }
        }
        
        // Route selected controls
        if (currentState is MapViewState.RouteSelected) {
            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(20.dp)
                    .fillMaxWidth()
            ) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(20.dp)
                    ) {
                        Text(
                            text = "Route to ${currentState.currentLocation.name}",
                            style = MaterialTheme.typography.headlineSmall,
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.padding(bottom = 8.dp)
                        )
                        
                        Text(
                            text = "${formatDuration(currentState.selectedRoute.endTime - currentState.selectedRoute.startTime)} • ${formatTime(currentState.selectedRoute.startTime)} - ${formatTime(currentState.selectedRoute.endTime)}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                            modifier = Modifier.padding(bottom = 16.dp)
                        )
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = { viewModel.startSimulation() },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("Simulate")
                            }
                            
                            OutlinedButton(
                                onClick = { viewModel.goBack() },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("Back")
                            }
                        }
                    }
                }
            }
        }
        
        // Delay report bottom sheet
        if (currentState is MapViewState.DelayReporting) {
            ModalBottomSheet(
                onDismissRequest = { viewModel.hideDelayReport() },
                sheetState = bottomSheetState,
                containerColor = MaterialTheme.colorScheme.surface,
                contentColor = MaterialTheme.colorScheme.onSurface,
                dragHandle = {
                    Box(
                        modifier = Modifier
                            .padding(vertical = 12.dp)
                            .width(32.dp)
                            .height(4.dp)
                            .background(
                                MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f),
                                RoundedCornerShape(2.dp)
                            )
                    )
                }
            ) {
                DelayReportBottomSheetContent(
                    currentState = currentState,
                    onSubmitReport = { trip, delayMinutes ->
                        viewModel.submitDelayReport(trip, delayMinutes)
                    },
                    onDismiss = { viewModel.hideDelayReport() }
                )
            }
        }
        
        // Simulation view (simplified)
        if (currentState is MapViewState.Simulating) {
            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(20.dp)
                    .fillMaxWidth()
            ) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(20.dp)
                    ) {
                        Text(
                            text = "Route to ${currentState.currentLocation.name}",
                            style = MaterialTheme.typography.headlineSmall,
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.padding(bottom = 8.dp)
                        )
                        
                        Text(
                            text = "${formatDuration(currentState.selectedRoute.endTime - currentState.selectedRoute.startTime)} • ${formatTime(currentState.selectedRoute.startTime)} - ${formatTime(currentState.selectedRoute.endTime)}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                            modifier = Modifier.padding(bottom = 16.dp)
                        )
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            OutlinedButton(
                                onClick = { viewModel.showDelayReport() },
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Warning,
                                    contentDescription = "Report Delay",
                                    modifier = Modifier.size(16.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("Delay")
                            }
                            
                            Button(
                                onClick = { viewModel.stopSimulation() },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("Exit")
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SearchBarTrigger(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
    isLoading: Boolean = false
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = 4.dp,
            pressedElevation = 6.dp
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier
                        .size(20.dp)
                        .padding(end = 12.dp),
                    strokeWidth = 2.dp,
                    color = MaterialTheme.colorScheme.primary
                )
            } else {
                Icon(
                    imageVector = Icons.Default.Search,
                    contentDescription = "Search",
                    tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                    modifier = Modifier.padding(end = 12.dp)
                )
            }
            Text(
                text = if (isLoading) "Finding routes..." else "Where to?",
                color = if (isLoading) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                style = MaterialTheme.typography.bodyLarge
            )
        }
    }
}

@Composable
fun SearchBottomSheetContent(
    mapViewportState: MapViewportState,
    onLocationSelected: (Suggestion, MapboxSearchService) -> Unit = { _, _ -> },
    onDismiss: () -> Unit = {}
) {
    var searchQuery by remember { mutableStateOf("") }
    var searchResults by remember { mutableStateOf<List<Suggestion>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val keyboardController = LocalSoftwareKeyboardController.current
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val searchService = remember { MapboxSearchService(context) }

    fun performSearch(query: String) {
        if (query.isBlank()) {
            searchResults = emptyList()
            return
        }
        
        isLoading = true
        errorMessage = null
        
        scope.launch {
            try {
                val currentCenter = mapViewportState.cameraState?.center
                val proximity = currentCenter?.let { "${it.longitude()},${it.latitude()}" }
                searchService.suggest(query, proximity).fold(
                    onSuccess = { results ->
                        searchResults = results
                        isLoading = false
                    },
                    onFailure = { exception ->
                        errorMessage = exception.message ?: "Search failed"
                        isLoading = false
                        searchResults = emptyList()
                    }
                )
            } catch (e: Exception) {
                errorMessage = "Failed to initialize search service: ${e.message}"
                isLoading = false
                searchResults = emptyList()
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp)
            .padding(bottom = 32.dp)
    ) {
        // Search input field
        OutlinedTextField(
            value = searchQuery,
            onValueChange = { 
                searchQuery = it
                if (it.length >= 3) {
                    performSearch(it)
                } else {
                    searchResults = emptyList()
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 20.dp),
            placeholder = {
                Text(
                    "Search for places",
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
            },
            leadingIcon = {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp
                    )
                } else {
                    Icon(
                        imageVector = Icons.Default.Search,
                        contentDescription = "Search",
                        tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                    )
                }
            },
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = MaterialTheme.colorScheme.primary,
                unfocusedBorderColor = MaterialTheme.colorScheme.outline,
                cursorColor = MaterialTheme.colorScheme.primary,
                focusedTextColor = MaterialTheme.colorScheme.onSurface,
                unfocusedTextColor = MaterialTheme.colorScheme.onSurface
            ),
            shape = RoundedCornerShape(16.dp),
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
            keyboardActions = KeyboardActions(
                onSearch = {
                    performSearch(searchQuery)
                    keyboardController?.hide()
                }
            )
        )

        // Error message
        errorMessage?.let { error ->
            Text(
                text = error,
                color = MaterialTheme.colorScheme.error,
                fontSize = 14.sp,
                modifier = Modifier.padding(bottom = 8.dp)
            )
        }

        // Search results
        if (searchResults.isNotEmpty()) {
            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(searchResults) { result ->
                    SearchResultItem(
                        result = result,
                        onClick = { onLocationSelected(result, searchService) }
                    )
                }
            }
        } else if (searchQuery.isEmpty()) {
            // Quick action buttons when no search
            Column(
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = "Quick Actions",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.padding(bottom = 16.dp)
                )

                QuickActionItem(
                    text = "Home",
                    onClick = { performSearch("Home") }
                )

                QuickActionItem(
                    text = "Work",
                    onClick = { performSearch("Work") }
                )

                QuickActionItem(
                    text = "Restaurant",
                    onClick = { performSearch("Restaurant") }
                )
            }
        }
    }
}

@Composable
fun SearchResultItem(
    result: Suggestion,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = 1.dp,
            pressedElevation = 3.dp
        ),
        shape = RoundedCornerShape(12.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Default.LocationOn,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(end = 16.dp)
            )
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = result.name,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface
                )
                result.fullAddress?.let { address ->
                    Text(
                        text = address,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
        }
    }
}

@Composable
fun QuickActionItem(
    text: String,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .padding(vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = Icons.Default.Search,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
            modifier = Modifier.padding(end = 16.dp)
        )
        Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
fun RoutesBottomSheetContent(
    routes: List<Itinerary>,
    destination: String,
    onRouteSelected: (Itinerary) -> Unit,
    onDismiss: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp)
            .padding(bottom = 32.dp)
    ) {
        // Header
        Text(
            text = "Routes to $destination",
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.padding(bottom = 20.dp)
        )
        
        if (routes.isEmpty()) {
            Text(
                text = "No routes found",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                modifier = Modifier.padding(vertical = 32.dp)
            )
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(vertical = 8.dp)
            ) {
                val sortedRoutes = routes.sortedBy { it.endTime - it.startTime }
                items(sortedRoutes.take(5)) { route -> // Limit to 5 routes, sorted by duration
                    RouteItem(
                        route = route,
                        onClick = { onRouteSelected(route) }
                    )
                }
            }
        }
    }
}

@Composable
fun RouteItem(
    route: Itinerary,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = 2.dp,
            pressedElevation = 4.dp
        ),
        shape = RoundedCornerShape(16.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            // Route summary
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = formatDuration(route.endTime - route.startTime),
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = formatTime(route.startTime) + " - " + formatTime(route.endTime),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                )
            }
            
            // Route modes
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                route.legs.forEach { leg ->
                    RouteMode(mode = leg.mode)
                }
            }
            
            // Route details
            if (route.legs.any { it.routeShortName != null }) {
                Text(
                    text = route.legs.mapNotNull { leg ->
                        if (leg.mode == "TRANSIT" && leg.routeShortName != null) {
                            leg.routeShortName
                        } else null
                    }.joinToString(", "),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                    modifier = Modifier.padding(top = 8.dp)
                )
            }
        }
    }
}

@Composable
fun RouteMode(mode: String) {
    val (icon, color) = when (mode) {
        "WALK" -> "🚶" to MaterialTheme.colorScheme.secondary
        "TRANSIT" -> "🚌" to MaterialTheme.colorScheme.primary
        "BUS" -> "🚌" to MaterialTheme.colorScheme.primary
        "TRAM" -> "🚋" to MaterialTheme.colorScheme.tertiary
        "SUBWAY" -> "🚇" to MaterialTheme.colorScheme.secondary
        else -> "🚶" to MaterialTheme.colorScheme.outline
    }
    
    Text(
        text = icon,
        fontSize = 16.sp,
        modifier = Modifier
            .background(
                color.copy(alpha = 0.12f),
                shape = RoundedCornerShape(8.dp)
            )
            .padding(horizontal = 8.dp, vertical = 4.dp)
    )
}

fun formatDuration(durationMillis: Long): String {
    val totalMinutes = (durationMillis / 1000 / 60).toInt()
    val hours = totalMinutes / 60
    val minutes = totalMinutes % 60
    
    return when {
        hours > 0 && minutes > 0 -> "${hours}h ${minutes}min"
        hours > 0 && minutes == 0 -> "${hours}h"
        minutes == 1 -> "1 min"
        else -> "$minutes min"
    }
}

fun formatTime(timeMillis: Long): String {
    val date = java.util.Date(timeMillis)
    val format = java.text.SimpleDateFormat("HH:mm", java.util.Locale.getDefault())
    return format.format(date)
}

// Polyline decoding function for Google's encoded polylines
fun decodePolyline(encoded: String): List<Point> {
    val points = mutableListOf<Point>()
    var index = 0
    val len = encoded.length
    var lat = 0
    var lng = 0

    while (index < len) {
        var b: Int
        var shift = 0
        var result = 0
        do {
            b = encoded[index++].code - 63
            result = result or (b and 0x1f shl shift)
            shift += 5
        } while (b >= 0x20)
        val dlat = if (result and 1 != 0) (result shr 1).inv() else result shr 1
        lat += dlat

        shift = 0
        result = 0
        do {
            b = encoded[index++].code - 63
            result = result or (b and 0x1f shl shift)
            shift += 5
        } while (b >= 0x20)
        val dlng = if (result and 1 != 0) (result shr 1).inv() else result shr 1
        lng += dlng

        points.add(Point.fromLngLat(lng / 1E5, lat / 1E5))
    }
    return points
}

@Composable
fun DelayReportBottomSheetContent(
    currentState: MapViewState.DelayReporting,
    onSubmitReport: (TripPOI, Int) -> Unit,
    onDismiss: () -> Unit
) {
    var selectedTrip by remember { mutableStateOf<TripPOI?>(null) }
    var delayMinutes by remember { mutableStateOf("") }
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp)
            .padding(bottom = 32.dp)
    ) {
        // Header
        Text(
            text = "Report Delay",
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.padding(bottom = 20.dp)
        )
        
        // Current route section (if public transport)
        currentState.selectedRoute?.let { route ->
            val transitLegs = route.legs.filter { it.mode == "TRANSIT" && it.routeShortName != null }
            if (transitLegs.isNotEmpty()) {
                Text(
                    text = "Current Route",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.padding(bottom = 12.dp)
                )
                
                transitLegs.forEach { leg ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { 
                                selectedTrip = currentState.nearbyTrips.find { leg.routeShortName == it.route.shortName }
                            }
                            .padding(bottom = 8.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = if (selectedTrip?.route?.gtfsId == leg.routeGtfsId)
                                MaterialTheme.colorScheme.primaryContainer 
                            else MaterialTheme.colorScheme.surface
                        ),
                        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = getTransportIcon(leg.mode),
                                fontSize = 20.sp,
                                modifier = Modifier.padding(end = 12.dp)
                            )
                            Column {
                                Text(
                                    text = leg.routeShortName ?: "Unknown Route",
                                    style = MaterialTheme.typography.bodyLarge,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                Text(
                                    text = leg.from.name,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                                )
                            }
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
        
        if (currentState.isLoadingTrips) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (currentState.nearbyTrips.isEmpty()) {
            Text(
                text = "No nearby trips found",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                modifier = Modifier.padding(vertical = 16.dp)
            )
        } else {
            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(currentState.nearbyTrips) { trip ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { selectedTrip = trip },
                        colors = CardDefaults.cardColors(
                            containerColor = when {
                                selectedTrip?.route?.gtfsId == trip.route.gtfsId -> MaterialTheme.colorScheme.primaryContainer
                                else -> MaterialTheme.colorScheme.surface
                            }
                        ),
                        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = getTransportIcon("TRANSIT"),
                                fontSize = 20.sp,
                                modifier = Modifier.padding(end = 12.dp)
                            )
                            Column(modifier = Modifier.weight(1f)) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Text(
                                        text = trip.route.shortName ?: trip.route.longName ?: "Unknown Route",
                                        style = MaterialTheme.typography.bodyLarge,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                    if (trip.isCurrentTrip) {
                                        Text(
                                            text = "CURRENT",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.primary,
                                            modifier = Modifier
                                                .background(
                                                    MaterialTheme.colorScheme.primaryContainer,
                                                    RoundedCornerShape(4.dp)
                                                )
                                                .padding(horizontal = 6.dp, vertical = 2.dp)
                                        )
                                    }
                                }
                                Text(
                                    text = "at ${trip.nearestStop.name}",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                                )
                                Text(
                                    text = "${trip.nearestStop.distance}m away",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f),
                                    modifier = Modifier.padding(top = 2.dp)
                                )
                            }
                        }
                    }
                }
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Delay minutes input
        OutlinedTextField(
            value = delayMinutes,
            onValueChange = { if (it.all { char -> char.isDigit() } && it.length <= 3) delayMinutes = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Delay in minutes") },
            placeholder = { Text("e.g. 15") },
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
            shape = RoundedCornerShape(16.dp)
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Submit button
        Button(
            onClick = { 
                selectedTrip?.let { trip ->
                    val minutes = delayMinutes.toIntOrNull() ?: 0
                    onSubmitReport(trip, minutes)
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = selectedTrip != null && delayMinutes.isNotBlank()
        ) {
            Text("Submit Delay Report")
        }
    }
}

fun getTransportIcon(mode: String): String {
    return when (mode) {
        "WALK" -> "🚶"
        "TRANSIT" -> "🚌"
        "BUS" -> "🚌"
        "TRAM" -> "🚋"
        "SUBWAY" -> "🚇"
        else -> "🚌"
    }
}

data class MapBounds(val center: Point, val northEast: Point, val southWest: Point)

fun calculateBounds(points: List<Point>): MapBounds {
    if (points.isEmpty()) {
        return MapBounds(
            center = Point.fromLngLat(0.0, 0.0),
            northEast = Point.fromLngLat(0.0, 0.0),
            southWest = Point.fromLngLat(0.0, 0.0)
        )
    }
    
    val minLat = points.minOf { it.latitude() }
    val maxLat = points.maxOf { it.latitude() }
    val minLng = points.minOf { it.longitude() }
    val maxLng = points.maxOf { it.longitude() }
    
    val centerLat = (minLat + maxLat) / 2
    val centerLng = (minLng + maxLng) / 2
    
    return MapBounds(
        center = Point.fromLngLat(centerLng, centerLat),
        northEast = Point.fromLngLat(maxLng, maxLat),
        southWest = Point.fromLngLat(minLng, minLat)
    )
}

