package com.example.denisplanner.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.example.denisplanner.service.BackendService
import com.example.denisplanner.service.Location
import com.example.denisplanner.service.Itinerary
import com.example.denisplanner.service.OTPService
import com.example.denisplanner.service.Suggestion
import com.example.denisplanner.service.MapboxSearchService
import com.example.denisplanner.service.POI
import com.example.denisplanner.service.TripPOI
import com.mapbox.geojson.Point
import kotlinx.coroutines.launch

sealed class MapViewState {
    data class Home(
        val showBottomSheet: Boolean = false
    ) : MapViewState()

    data class SearchingLocation(
        val isLoadingRoutes: Boolean = false
    ) : MapViewState()

    data class RouteOverview(
        val currentLocation: Location,
        val routes: List<Itinerary>,
    ) : MapViewState()

    data class RouteSelected(
        val currentLocation: Location,
        val selectedRoute: Itinerary,
    ) : MapViewState()

    data class Simulating(
        val currentLocation: Location,
        val selectedRoute: Itinerary,
        val isSimulating: Boolean = false
    ) : MapViewState()

    data class DelayReporting(
        val currentLocation: Location,
        val selectedRoute: Itinerary?,
        val nearbyTrips: List<TripPOI> = emptyList(),
        val isLoadingTrips: Boolean = false
    ) : MapViewState()
}

data class MapUiData(
    val stateStack: List<MapViewState> = listOf(MapViewState.Home()),
    val errorMessage: String? = null
) {
    val currentState: MapViewState get() = stateStack.last()
    val canGoBack: Boolean get() = stateStack.size > 1
}

class MapViewModel : ViewModel() {
    private val otpService = OTPService()

    public val backendService = BackendService()

    var uiData by mutableStateOf(MapUiData())
        private set

    var currentPuckLocation by mutableStateOf<Point?>(null)

    val currentState: MapViewState get() = uiData.currentState
    val canGoBack: Boolean get() = uiData.canGoBack

    // State stack management
    private fun pushState(newState: MapViewState) {
        uiData = uiData.copy(stateStack = uiData.stateStack + newState)
    }

    private fun replaceCurrentState(newState: MapViewState) {
        val newStack = uiData.stateStack.dropLast(1) + newState
        uiData = uiData.copy(stateStack = newStack)
    }

    fun goBack(): Boolean {
        return if (canGoBack) {
            val newStack = uiData.stateStack.dropLast(1)
            uiData = uiData.copy(stateStack = newStack)
            true
        } else {
            false
        }
    }

    fun updatePuckLocation(location: Point) {
        currentPuckLocation = location
    }

    fun showBottomSheet() {
        when (val current = currentState) {
            is MapViewState.Home -> {
                replaceCurrentState(current.copy(showBottomSheet = true))
            }
            else -> {
                // Push a new searching state
                pushState(MapViewState.SearchingLocation())
            }
        }
    }

    fun hideBottomSheet() {
        when (currentState) {
            is MapViewState.Home -> {
                replaceCurrentState((currentState as MapViewState.Home).copy(showBottomSheet = false))
            }
            is MapViewState.SearchingLocation -> {
                // Go back to home state instead of using goBack() which might cause issues
                uiData = uiData.copy(stateStack = listOf(MapViewState.Home()))
            }
            else -> { /* Do nothing for other states */ }
        }
    }

    fun selectLocation(suggestion: Suggestion, searchService: MapboxSearchService) {
        // Set loading state
        replaceCurrentState(MapViewState.SearchingLocation(
            isLoadingRoutes = true
        ))

        viewModelScope.launch {
            try {
                searchService.retrieve(suggestion).fold(
                    onSuccess = { location ->
                        planRouteFromCurrentLocation(location)
                    },
                    onFailure = { exception ->
                        uiData = uiData.copy(
                            errorMessage = "Failed to get location details: ${exception.message}"
                        )
                    }
                )
            } catch (e: Exception) {
                uiData = uiData.copy(errorMessage = "Error: ${e.message}")
            }
        }
    }

    private fun planRouteFromCurrentLocation(destination: Location) {
        val userLocation = currentPuckLocation
        if (userLocation != null) {
            planTrip(
                fromLat = userLocation.latitude(),
                fromLon = userLocation.longitude(),
                toLat = destination.latitude,
                toLon = destination.longitude,
                destination = destination
            )
        } else {
            uiData = uiData.copy(
                errorMessage = "Current location not available"
            )
        }
    }

    private fun planTrip(fromLat: Double, fromLon: Double, toLat: Double, toLon: Double, destination: Location) {
        viewModelScope.launch {
            try {
                val response = otpService.planTrip(
                    fromLat = fromLat,
                    fromLon = fromLon,
                    toLat = toLat,
                    toLon = toLon
                )
                
                // Replace current state with route overview
                replaceCurrentState(MapViewState.RouteOverview(
                    currentLocation = destination,
                    routes = response.itineraries,
                ))
            } catch (e: Exception) {
                uiData = uiData.copy(
                    errorMessage = "Failed to plan route: ${e.message}"
                )
            }
        }
    }

    fun selectRoute(route: Itinerary) {
        val currentLocation = when (val state = currentState) {
            is MapViewState.RouteOverview -> state.currentLocation
            else -> null
        }
        
        if (currentLocation != null) {
            pushState(MapViewState.RouteSelected(
                currentLocation = currentLocation,
                selectedRoute = route,
            ))
        }
    }

    fun startSimulation() {
        val currentLocation = when (val state = currentState) {
            is MapViewState.RouteSelected -> state.currentLocation
            else -> null
        }
        val selectedRoute = when (val state = currentState) {
            is MapViewState.RouteSelected -> state.selectedRoute
            else -> null
        }
        
        if (currentLocation != null && selectedRoute != null) {
            pushState(MapViewState.Simulating(
                currentLocation = currentLocation,
                selectedRoute = selectedRoute,
                isSimulating = false
            ))
        }
    }

    fun stopSimulation() {
        when (currentState) {
            is MapViewState.Simulating -> goBack()
            else -> { /* Do nothing */ }
        }
    }

    fun clearError() {
        uiData = uiData.copy(errorMessage = null)
    }
    
    fun goToHome() {
        uiData = uiData.copy(stateStack = listOf(MapViewState.Home()))
    }

    fun showDelayReport() {
        val currentLocation = when (val state = currentState) {
            is MapViewState.Simulating -> state.currentLocation
            is MapViewState.RouteSelected -> state.currentLocation
            else -> null
        }
        val selectedRoute = when (val state = currentState) {
            is MapViewState.Simulating -> state.selectedRoute
            is MapViewState.RouteSelected -> state.selectedRoute
            else -> null
        }
        
        if (currentLocation != null) {
            pushState(MapViewState.DelayReporting(
                currentLocation = currentLocation,
                selectedRoute = selectedRoute,
                isLoadingTrips = true
            ))
            loadNearbyTrips(selectedRoute)
        }
    }

    fun hideDelayReport() {
        when (currentState) {
            is MapViewState.DelayReporting -> goBack()
            else -> { /* Do nothing */ }
        }
    }

    private fun loadNearbyTrips(selectedRoute: Itinerary?) {
        val userLocation = currentPuckLocation
        if (userLocation != null) {
            viewModelScope.launch {
                try {
                    val currentRouteGtfsIds = selectedRoute?.legs
                        ?.mapNotNull { it.routeGtfsId }
                        ?: emptyList()
                    
                    val trips = otpService.fetchUniqueTripsInRadius(
                        latitude = userLocation.latitude(),
                        longitude = userLocation.longitude(),
                        radiusMeters = 1000,
                        currentRouteGtfsIds = currentRouteGtfsIds
                    )
                    
                    if (currentState is MapViewState.DelayReporting) {
                        replaceCurrentState((currentState as MapViewState.DelayReporting).copy(
                            nearbyTrips = trips,
                            isLoadingTrips = false
                        ))
                    }
                } catch (e: Exception) {
                    uiData = uiData.copy(
                        errorMessage = "Failed to load nearby trips: ${e.message}"
                    )
                    if (currentState is MapViewState.DelayReporting) {
                        replaceCurrentState((currentState as MapViewState.DelayReporting).copy(
                            isLoadingTrips = false
                        ))
                    }
                }
            }
        } else {
            uiData = uiData.copy(
                errorMessage = "Current location not available"
            )
        }
    }

    fun submitDelayReport(trip: TripPOI, delayMinutes: Int) {
        val userLocation = currentPuckLocation

        if (userLocation != null) {
            viewModelScope.launch {
                try {
                    val report = com.example.denisplanner.service.Report(
                        userName = "demo",
                        userLocation = listOf(userLocation.latitude().toFloat(), userLocation.longitude().toFloat()),
                        locationPos = listOf(trip.nearestStop.latitude.toFloat(), trip.nearestStop.longitude.toFloat()),
                        locationName = trip.route.gtfsId + "@" + trip.nearestStop.stopId,
                        reportType = com.example.denisplanner.service.ReportType.DELAY,
                        delayMinutes = delayMinutes
                    )
                    
                    backendService.sendReport(report)
                    hideDelayReport()
                    uiData = uiData.copy(
                        errorMessage = "Delay report submitted successfully"
                    )
                } catch (e: Exception) {
                    uiData = uiData.copy(
                        errorMessage = "Failed to submit delay report: ${e.message}"
                    )
                }
            }
        }
    }
}