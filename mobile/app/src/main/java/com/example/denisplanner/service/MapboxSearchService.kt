package com.example.denisplanner.service

import android.content.Context
import com.example.denisplanner.R
import com.squareup.moshi.Json
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.logging.HttpLoggingInterceptor
import java.io.IOException

data class MapboxSuggestResponse(
    @Json(name = "suggestions") val suggestions: List<Suggestion>
)

data class MapboxRetrieveResponse(
    @Json(name = "features") val features: List<Feature>,
)

data class Suggestion(
    @Json(name = "name") val name: String,
    @Json(name = "full_address") val fullAddress: String?,
    @Json(name = "mapbox_id") val mapboxId: String,
)

data class Feature(
    @Json(name = "geometry") val geometry: Geometry,
)

data class Geometry(
    @Json(name = "coordinates") val coordinates: List<Double>
)

data class Location(
    val name: String,
    val fullAddress: String?,
    val longitude: Double,
    val latitude: Double
)

class MapboxSearchService(private val context: Context) {
    private val client: OkHttpClient
    private val moshi = Moshi.Builder()
        .add(KotlinJsonAdapterFactory())
        .build()
    private val accessToken = context.getString(R.string.mapbox_access_token)

    init {
        val logging = HttpLoggingInterceptor()
        logging.setLevel(HttpLoggingInterceptor.Level.BASIC)

        client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()
    }

    suspend fun suggest(
        query: String,
        proximity: String? = null,
        limit: Int = 10
    ): Result<List<Suggestion>> = withContext(Dispatchers.IO) {
        try {
            val url = "https://api.mapbox.com/search/searchbox/v1/suggest".toHttpUrl().newBuilder()
                .addQueryParameter("q", query)
                .addQueryParameter("access_token", accessToken)
                .addQueryParameter("session_token", "d9e7b439-418f-4e50-b25d-2e3c363a631a")
                .apply {
                    proximity?.let { addQueryParameter("proximity", it) }
                }
                .addQueryParameter("country", "pl")
                .addQueryParameter("limit", limit.toString())
                .build()

            val request = Request.Builder().url(url).build()

            val response = client.newCall(request).execute()

            if (!response.isSuccessful) {
                throw IOException("Unexpected code $response")
            }

            val responseBody = response.body?.string()
            if (responseBody == null) {
                throw IOException("Empty response body")
            }

            val adapter = moshi.adapter(MapboxSuggestResponse::class.java)
            val searchResponse = adapter.fromJson(responseBody)
                ?: throw IOException("Failed to parse response")

            Result.success(searchResponse.suggestions)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun retrieve(
        suggestion: Suggestion
    ): Result<Location> = withContext(Dispatchers.IO) {
        try {
            val url =
                ("https://api.mapbox.com/search/searchbox/v1/retrieve/" + suggestion.mapboxId).toHttpUrl()
                    .newBuilder()
                    .addQueryParameter("access_token", accessToken)
                    .addQueryParameter("session_token", "d9e7b439-418f-4e50-b25d-2e3c363a631a")
                    .build()

            val request = Request.Builder().url(url).build()

            val response = client.newCall(request).execute()

            if (!response.isSuccessful) {
                throw IOException("Unexpected code $response")
            }

            val responseBody = response.body?.string()
            if (responseBody == null) {
                throw IOException("Empty response body")
            }

            val adapter = moshi.adapter(MapboxRetrieveResponse::class.java)
            val searchResponse = adapter.fromJson(responseBody)
                ?: throw IOException("Failed to parse response")

            val loc = Location(
                suggestion.name,
                suggestion.fullAddress,
                searchResponse.features[0].geometry.coordinates[0],
                searchResponse.features[0].geometry.coordinates[1]
            )

            Result.success(loc)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}