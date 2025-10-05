package com.example.denisplanner.location

import com.mapbox.geojson.LineString
import com.mapbox.geojson.Point
import com.mapbox.maps.plugin.locationcomponent.LocationConsumer
import com.mapbox.maps.plugin.locationcomponent.LocationProvider
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.concurrent.CopyOnWriteArraySet
import kotlin.math.*

/**
 * A location provider implementation that takes in a line string as route and animate the location
 * updates along the route.
 */
class SimulateRouteLocationProvider(
    private val route: LineString,
    private val startingLocation: Point? = null,
    private val updateIntervalMs: Long = 1000L
) : LocationProvider {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var emitLocationsJob: Job? = null
    private val totalRouteLength by lazy { calculateRouteLength(route) }
    private val routeCoordinates = route.coordinates()
    private val locationConsumers = CopyOnWriteArraySet<LocationConsumer>()
    private var isFakeLocationEmitting = false
    
    // Position-based movement
    private var currentProgress = 0.0 // 0.0 to 1.0
    private val progressStep = 0.01 // Move 1% of route per update
    private var currentBearing = 0.0

    override fun registerLocationConsumer(locationConsumer: LocationConsumer) {
        locationConsumers.add(locationConsumer)
        if (!isFakeLocationEmitting) {
            emitFakeLocations()
            isFakeLocationEmitting = true
        }
    }

    override fun unRegisterLocationConsumer(locationConsumer: LocationConsumer) {
        locationConsumers.remove(locationConsumer)
        if (locationConsumers.isEmpty()) {
            emitLocationsJob?.cancel()
            isFakeLocationEmitting = false
        }
    }

    fun startSimulation() {
        if (!isFakeLocationEmitting && locationConsumers.isNotEmpty()) {
            emitFakeLocations()
            isFakeLocationEmitting = true
        }
    }

    fun stopSimulation() {
        emitLocationsJob?.cancel()
        isFakeLocationEmitting = false
    }

    fun isSimulating(): Boolean = isFakeLocationEmitting
    
    // Set progress manually (0.0 to 1.0)
    fun setProgress(progress: Double) {
        currentProgress = maxOf(0.0, minOf(1.0, progress))
        if (isFakeLocationEmitting) {
            val currentLocation = interpolatePositionOnRoute(currentProgress)
            scope.launch(Dispatchers.Main) {
                locationConsumers.forEach { it.onLocationUpdated(currentLocation) }
                locationConsumers.forEach { it.onBearingUpdated(currentBearing) }
            }
        }
    }
    
    // Set bearing manually
    fun setBearing(bearing: Double) {
        currentBearing = bearing
        if (isFakeLocationEmitting) {
            scope.launch(Dispatchers.Main) {
                locationConsumers.forEach { it.onBearingUpdated(currentBearing) }
            }
        }
    }
    
    // Get current progress
    fun getCurrentProgress(): Double = currentProgress

    private fun emitFakeLocations() {
        val previousEmitLocationsJob = emitLocationsJob
        emitLocationsJob = scope.launch {
            // Make sure previous job is cancelled before starting a new one
            previousEmitLocationsJob?.cancelAndJoin()
            
            // Start with the provided starting location or first route point
            val startPoint = startingLocation ?: routeCoordinates.firstOrNull() ?: Point.fromLngLat(0.0, 0.0)
            
            // Initialize bearing if we have multiple points
            if (routeCoordinates.size > 1) {
                currentBearing = calculateBearing(startPoint, routeCoordinates[1])
            }
            
            // Emit starting location first
            withContext(Dispatchers.Main) {
                val startLocationWithProgress = Point.fromLngLat(
                    startPoint.longitude(), 
                    startPoint.latitude(), 
                    currentProgress
                )
                locationConsumers.forEach { it.onLocationUpdated(startLocationWithProgress) }
                locationConsumers.forEach { it.onBearingUpdated(currentBearing) }
            }
            
            while (isActive && currentProgress < 1.0) {
                currentProgress = minOf(1.0, currentProgress + progressStep)
                val currentLocation = interpolatePositionOnRoute(currentProgress)
                
                withContext(Dispatchers.Main) {
                    locationConsumers.forEach { it.onLocationUpdated(currentLocation) }
                    locationConsumers.forEach { it.onBearingUpdated(currentBearing) }
                }
                delay(updateIntervalMs)
            }
            
            // Simulation completed
            withContext(Dispatchers.Main) {
                isFakeLocationEmitting = false
            }
        }
    }

    // Interpolate position along route based on progress (0.0 to 1.0)
    private fun interpolatePositionOnRoute(progress: Double): Point {
        if (routeCoordinates.isEmpty()) {
            return Point.fromLngLat(0.0, 0.0, progress)
        }
        
        if (routeCoordinates.size == 1) {
            val point = routeCoordinates[0]
            return Point.fromLngLat(point.longitude(), point.latitude(), progress)
        }
        
        val targetDistance = progress * totalRouteLength
        var accumulatedDistance = 0.0
        
        for (i in 0 until routeCoordinates.size - 1) {
            val current = routeCoordinates[i]
            val next = routeCoordinates[i + 1]
            val segmentDistance = calculateDistance(current, next)
            
            if (accumulatedDistance + segmentDistance >= targetDistance) {
                // Interpolate within this segment
                val remainingDistance = targetDistance - accumulatedDistance
                val segmentProgress = if (segmentDistance > 0) remainingDistance / segmentDistance else 0.0
                
                val lat = current.latitude() + (next.latitude() - current.latitude()) * segmentProgress
                val lng = current.longitude() + (next.longitude() - current.longitude()) * segmentProgress
                
                return Point.fromLngLat(lng, lat, progress)
            }
            
            accumulatedDistance += segmentDistance
        }
        
        // Return last point if we've gone past the end
        val lastPoint = routeCoordinates.last()
        return Point.fromLngLat(lastPoint.longitude(), lastPoint.latitude(), progress)
    }

    private fun calculateDistanceFromStart(point: Point): Double {
        val routeCoordinates = route.coordinates()
        var distance = 0.0
        
        for (i in 0 until routeCoordinates.size - 1) {
            val current = routeCoordinates[i]
            val next = routeCoordinates[i + 1]
            
            // If we've reached our target point, add partial distance
            if (current == point) {
                break
            }
            
            distance += calculateDistance(current, next)
        }
        
        return distance
    }

    private fun calculateRouteLength(lineString: LineString): Double {
        val coordinates = lineString.coordinates()
        var totalLength = 0.0
        
        for (i in 0 until coordinates.size - 1) {
            totalLength += calculateDistance(coordinates[i], coordinates[i + 1])
        }
        
        return totalLength
    }

    private fun calculateDistance(point1: Point, point2: Point): Double {
        val earthRadius = 6371000.0 // Earth's radius in meters
        
        val lat1Rad = Math.toRadians(point1.latitude())
        val lat2Rad = Math.toRadians(point2.latitude())
        val deltaLatRad = Math.toRadians(point2.latitude() - point1.latitude())
        val deltaLngRad = Math.toRadians(point2.longitude() - point1.longitude())

        val a = sin(deltaLatRad / 2).pow(2) +
                cos(lat1Rad) * cos(lat2Rad) * sin(deltaLngRad / 2).pow(2)
        val c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earthRadius * c
    }

    private fun calculateBearing(from: Point, to: Point): Double {
        val lat1Rad = Math.toRadians(from.latitude())
        val lat2Rad = Math.toRadians(to.latitude())
        val deltaLngRad = Math.toRadians(to.longitude() - from.longitude())

        val y = sin(deltaLngRad) * cos(lat2Rad)
        val x = cos(lat1Rad) * sin(lat2Rad) - sin(lat1Rad) * cos(lat2Rad) * cos(deltaLngRad)

        val bearing = Math.toDegrees(atan2(y, x))
        return (bearing + 360) % 360
    }
}