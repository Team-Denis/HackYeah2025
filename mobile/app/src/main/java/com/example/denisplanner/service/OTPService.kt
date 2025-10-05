package com.example.denisplanner.service
import android.util.Log
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.logging.HttpLoggingInterceptor
import com.squareup.moshi.Json
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

const val URI = "https://otp.lucasahou.com"

class OTPService() {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        })
        .build()

    private val moshi = Moshi.Builder()
        .add(KotlinJsonAdapterFactory())
        .build()

    private val JSON = "application/json; charset=utf-8".toMediaType()

    suspend fun planTrip(
        fromLat: Double,
        fromLon: Double,
        toLat: Double,
        toLon: Double,
    ): OTPResponse = withContext(Dispatchers.IO) {

        val query = """
            {
                plan(
                    from: { lat: $fromLat, lon: $fromLon }
                    to: { lat: $toLat, lon: $toLon }
                    transportModes: [
                        {
                            mode: WALK
                        },
                        {
                            mode: TRANSIT
                        },
                    ]) {
                    itineraries {
                        startTime
                        endTime
                        legs {
                            mode
                            startTime
                            endTime
                            from {
                                name
                                lat
                                lon
                                departureTime
                                arrivalTime
                            }
                            to {
                                name
                                lat
                                lon
                                departureTime
                                arrivalTime
                            }
                            route {
                                gtfsId
                                longName
                                shortName
                            }
                            legGeometry {
                                points
                            }
                        }
                    }
                }
            }
        """.trimIndent()

        val requestBody = mapOf(
            "query" to query,
            "variables" to emptyMap<String, Any>()
        )

        val adapter = moshi.adapter(Map::class.java)
        val json = adapter.toJson(requestBody)

        val request = Request.Builder()
            .url("$URI/otp/routers/default/index/graphql")
            .post(json.toRequestBody(JSON))
            .build()

        val response = client.newCall(request).execute()
        val responseBody = response.body?.string() ?: throw Exception("Empty response")

        if (!response.isSuccessful) {
            throw Exception("HTTP ${response.code}: $responseBody")
        }

        parseOTPResponse(responseBody)
    }

    suspend fun fetchPOIsInRadius(
        latitude: Double,
        longitude: Double,
        radiusMeters: Int = 500
    ): List<POI> = withContext(Dispatchers.IO) {

        val query = """
            {
                stopsByRadius(lat: $latitude, lon: $longitude, radius: $radiusMeters) {
                    edges {
                        node {
                            stop {
                                gtfsId
                                name
                                lat
                                lon
                                code
                                desc
                                patterns {
                                    route {
                                        gtfsId
                                        shortName
                                        longName
                                    }
                                }
                            }
                            distance
                        }
                    }
                }
            }
        """.trimIndent()

        val requestBody = mapOf(
            "query" to query,
            "variables" to emptyMap<String, Any>()
        )

        val adapter = moshi.adapter(Map::class.java)
        val json = adapter.toJson(requestBody)

        val request = Request.Builder()
            .url("$URI/otp/routers/default/index/graphql")
            .post(json.toRequestBody(JSON))
            .build()

        val response = client.newCall(request).execute()
        val responseBody = response.body?.string() ?: throw Exception("Empty response")

        if (!response.isSuccessful) {
            throw Exception("HTTP ${response.code}: $responseBody")
        }

        parsePOIResponse(responseBody)
    }

    suspend fun fetchUniqueTripsInRadius(
        latitude: Double,
        longitude: Double,
        radiusMeters: Int = 500,
        currentRouteGtfsIds: List<String> = emptyList()
    ): List<TripPOI> = withContext(Dispatchers.IO) {
        val allStops = fetchPOIsInRadius(latitude, longitude, radiusMeters)
        
        // Group by route GTFS ID and find nearest stop for each route
        val routeToNearestStop = mutableMapOf<String, POI>()
        
        allStops.forEach { stop ->
            stop.routes.forEach { route ->
                val existingStop = routeToNearestStop[route.gtfsId]
                if (existingStop == null || stop.distance < existingStop.distance) {
                    routeToNearestStop[route.gtfsId] = stop
                }
            }
        }
        
        // Convert to TripPOI list with current trip prioritization
        val trips = routeToNearestStop.flatMap { (gtfsId, stop) ->
            stop.routes.filter { it.gtfsId == gtfsId }.map { route ->
                TripPOI(
                    route = route,
                    nearestStop = stop,
                    isCurrentTrip = currentRouteGtfsIds.contains(route.gtfsId)
                )
            }
        }
        
        // Sort: current trips first, then by distance
        trips.sortedWith(
            compareBy<TripPOI> { !it.isCurrentTrip }
                .thenBy { it.nearestStop.distance }
        )
    }

    private fun parseOTPResponse(json: String): OTPResponse {
        val adapter = moshi.adapter(PlanTripGraphQLResponse::class.java)
        val graphQLResponse = adapter.fromJson(json)
            ?: throw Exception("Failed to parse response")

        if (graphQLResponse.errors != null) {
            throw Exception("GraphQL errors: ${graphQLResponse.errors}")
        }

        val plan = graphQLResponse.data?.plan
            ?: throw Exception("No plan data in response")

        val itineraryList = plan.itineraries.map { itinerary ->
            Itinerary(
                startTime = itinerary.startTime,
                endTime = itinerary.endTime,
                legs = itinerary.legs.map { leg ->
                    Leg(
                        mode = leg.mode,
                        startTime = leg.startTime,
                        endTime = leg.endTime,
                        from = RouteLocation(
                            name = leg.from.name,
                            latitude = leg.from.lat,
                            longitude = leg.from.lon,
                            fullAddress = null,
                            departureTime = leg.from.departureTime ?: 0,
                            arrivalTime = leg.from.arrivalTime ?: 0,
                        ),
                        to = RouteLocation(
                            name = leg.to.name,
                            latitude = leg.to.lat,
                            longitude = leg.to.lon,
                            fullAddress = null,
                            departureTime = leg.to.departureTime ?: 0,
                            arrivalTime = leg.to.arrivalTime ?: 0,
                        ),
                        routeGtfsId = leg.route?.gtfsId,
                        routeShortName = leg.route?.shortName,
                        routeLongName = leg.route?.longName,
                        legGeometry = leg.legGeometry.points
                    )
                }
            )
        }

        return OTPResponse(itineraryList)
    }

    private fun parsePOIResponse(json: String): List<POI> {
        val adapter = moshi.adapter(POIGraphQLResponse::class.java)
        val graphQLResponse = adapter.fromJson(json)
            ?: throw Exception("Failed to parse response")

        if (graphQLResponse.errors != null) {
            throw Exception("GraphQL errors: ${graphQLResponse.errors}")
        }

        val stopsByRadius = graphQLResponse.data?.stopsByRadius
            ?: throw Exception("No stopsByRadius data in response")

        return stopsByRadius.edges.map { edge ->
            val stop = edge.node.stop
            val routes = stop.patterns?.mapNotNull { pattern ->
                pattern.route?.let { route ->
                    RouteInfo(
                        gtfsId = route.gtfsId,
                        shortName = route.shortName,
                        longName = route.longName
                    )
                }
            }?.distinctBy { it.gtfsId } ?: emptyList()

            POI(
                stopId = stop.gtfsId,
                name = stop.name,
                latitude = stop.lat,
                longitude = stop.lon,
                code = stop.code,
                description = stop.desc,
                distance = edge.node.distance,
                routes = routes
            )
        }
    }
}

// Moshi data classes for GraphQL responses
private data class PlanTripGraphQLResponse(
    val data: PlanData?,
    val errors: List<Map<String, Any>>?
)

private data class PlanData(
    val plan: Plan
)

private data class Plan(
    val itineraries: List<ItineraryResponse>
)

private data class ItineraryResponse(
    val startTime: Long,
    val endTime: Long,
    val legs: List<LegResponse>
)

private data class LegResponse(
    val mode: String,
    val startTime: Long,
    val endTime: Long,
    val from: LocationResponse,
    val to: LocationResponse,
    val route: RouteResponse?,
    val legGeometry: GeometryResponse
)

private data class LocationResponse(
    val name: String,
    val lat: Double,
    val lon: Double,
    val departureTime: Long?,
    val arrivalTime: Long?,
)

private data class RouteResponse(
    val gtfsId: String,
    val shortName: String?,
    val longName: String?
)

private data class GeometryResponse(
    val points: String
)

private data class POIGraphQLResponse(
    val data: POIData?,
    val errors: List<Map<String, Any>>?
)

private data class POIData(
    val stopsByRadius: StopsByRadius
)

private data class StopsByRadius(
    val edges: List<StopEdge>
)

private data class StopEdge(
    val node: StopNode
)

private data class StopNode(
    val stop: StopResponse,
    val distance: Int
)

private data class StopResponse(
    val gtfsId: String,
    val name: String,
    val lat: Double,
    val lon: Double,
    val code: String?,
    val desc: String?,
    val patterns: List<PatternResponse>?
)

private data class PatternResponse(
    val route: RouteResponse?
)

// Public data classes
data class OTPResponse(val itineraries: List<Itinerary>)

data class Itinerary(
    val startTime: Long,
    val endTime: Long,
    val legs: List<Leg>
)

data class Leg(
    val mode: String,
    val startTime: Long,
    val endTime: Long,
    val from: RouteLocation,
    val to: RouteLocation,
    val routeGtfsId: String?,
    val routeShortName: String?,
    val routeLongName: String?,
    val legGeometry: String
)

data class RouteLocation(
    val name: String,
    val latitude: Double,
    val longitude: Double,
    val fullAddress: String?,
    val departureTime: Long = 0,
    val arrivalTime: Long = 0,
)

data class POI(
    val stopId: String,
    val name: String,
    val latitude: Double,
    val longitude: Double,
    val code: String?,
    val description: String?,
    val distance: Int, // Distance in meters from the query point
    val routes: List<RouteInfo> // All routes that serve this stop
)

data class RouteInfo(
    val gtfsId: String,
    val shortName: String?,
    val longName: String?
)

data class TripPOI(
    val route: RouteInfo,
    val nearestStop: POI,
    val isCurrentTrip: Boolean = false
)