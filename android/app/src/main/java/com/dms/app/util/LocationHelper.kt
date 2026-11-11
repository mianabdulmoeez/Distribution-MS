package com.dms.app.util

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.os.SystemClock
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

data class LocationFix(
    val lat: Double,
    val lng: Double,
    val accuracyMeters: Float,
    val fixAgeSeconds: Float,
    val isMock: Boolean,
    val deviceMonotonicTime: Long
)

class LocationHelper(private val context: Context) {

    private val fusedLocationClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)

    @SuppressLint("MissingPermission")
    suspend fun getFreshLocationFix(): Result<LocationFix> {
        return suspendCancellableCoroutine { continuation ->
            val cts = CancellationTokenSource()

            fusedLocationClient.getCurrentLocation(
                Priority.PRIORITY_HIGH_ACCURACY,
                cts.token
            ).addOnSuccessListener { location: Location? ->
                if (location != null) {
                    val nowNanos = SystemClock.elapsedRealtimeNanos()
                    val fixAgeNanos = nowNanos - location.elapsedRealtimeNanos
                    val fixAgeSeconds = (fixAgeNanos / 1_000_000_000.0).toFloat()

                    val isMock = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
                        location.isMock
                    } else {
                        @Suppress("DEPRECATION")
                        location.isFromMockProvider
                    }

                    continuation.resume(
                        Result.success(
                            LocationFix(
                                lat = location.latitude,
                                lng = location.longitude,
                                accuracyMeters = location.accuracy,
                                fixAgeSeconds = maxOf(0f, fixAgeSeconds),
                                isMock = isMock,
                                deviceMonotonicTime = SystemClock.elapsedRealtime()
                            )
                        )
                    )
                } else {
                    continuation.resume(Result.failure(Exception("Could not obtain GPS fix. Please ensure location services are enabled.")))
                }
            }.addOnFailureListener { e ->
                continuation.resume(Result.failure(e))
            }

            continuation.invokeOnCancellation {
                cts.cancel()
            }
        }
    }
}

