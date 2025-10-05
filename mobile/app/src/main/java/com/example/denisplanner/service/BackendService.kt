package com.example.denisplanner.service

import android.util.Log
import com.squareup.moshi.Json
import com.squareup.moshi.JsonAdapter
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.logging.HttpLoggingInterceptor

const val BACKEND_URI: String = "https://semiconservative-dentoid-sharika.ngrok-free.dev"

enum class ReportType {
    DELAY, MAINTENANCE, ACCIDENT, SOLVED, OTHER
}

data class Report(
    @Json(name = "user_name") val userName: String,
    @Json(name = "user_location") val userLocation: List<Float>,
    @Json(name = "location_pos") val locationPos: List<Float>,
    @Json(name = "location_name") val locationName: String,
    @Json(name = "report_type") val reportType: ReportType,
    @Json(name = "delay_minutes") val delayMinutes: Int?
)

class BackendService {
    val moshi: Moshi = Moshi.Builder()
        .add(KotlinJsonAdapterFactory())
        .build()

    val client: OkHttpClient

    init {
        val logging = HttpLoggingInterceptor()
        logging.setLevel(HttpLoggingInterceptor.Level.BASIC)

        client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()
    }

    suspend fun sendReport(report: Report): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            Log.e("AAA", report.toString())

            val jsonAdapter: JsonAdapter<Report> = moshi.adapter(Report::class.java)
            val json: String = jsonAdapter.toJson(report)

            val body = json.toRequestBody("application/json".toMediaTypeOrNull())
            val request = Request.Builder().url("$BACKEND_URI/enqueue").post(body).build()

            val response = client.newCall(request).execute()

            Log.e("AAA", response.toString())  // This should now print

            if (!response.isSuccessful) {
                Result.failure(Exception("HTTP ${response.code}"))
            } else {
                Result.success(Unit)
            }
        } catch (e: Exception) {
            Log.e("AAA", "Exception: ${e.message}")
            Result.failure(e)
        }
    }
}
