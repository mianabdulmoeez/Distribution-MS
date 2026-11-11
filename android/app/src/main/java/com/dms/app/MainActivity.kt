package com.dms.app

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.lifecycleScope
import com.dms.app.data.api.RetrofitClient
import com.dms.app.data.model.*
import com.dms.app.ui.screens.*
import com.dms.app.util.LocationHelper
import kotlinx.coroutines.launch
import java.util.UUID

enum class Screen {
    LOGIN,
    TODAY_STOPS,
    VISIT_OUTCOME,
    ORDER_FORM
}

class MainActivity : ComponentActivity() {

    private lateinit var locationHelper: LocationHelper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        locationHelper = LocationHelper(this)

        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    MainAppNav()
                }
            }
        }
    }

    @Composable
    fun MainAppNav() {
        var currentScreen by remember { mutableStateOf(Screen.LOGIN) }
        var authUser by remember { mutableStateOf<AuthUser?>(null) }
        var stops by remember { mutableStateOf<List<TodayShopItem>>(emptyList()) }
        var selectedShop by remember { mutableStateOf<Shop?>(null) }
        var currentVisitId by remember { mutableStateOf<String?>(null) }
        var currentGrantId by remember { mutableStateOf<String?>(null) }
        var isLoading by remember { mutableStateOf(false) }
        var errorMessage by remember { mutableStateOf<String?>(null) }

        val refreshStops = {
            isLoading = true
            lifecycleScope.launch {
                try {
                    val response = RetrofitClient.apiService.getTodayStops()
                    if (response.isSuccessful) {
                        stops = response.body() ?: emptyList()
                    }
                } catch (e: Exception) {
                    Toast.makeText(this@MainActivity, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                } finally {
                    isLoading = false
                }
            }
        }

        when (currentScreen) {
            Screen.LOGIN -> {
                LoginScreen(
                    onLoginSuccess = { currentScreen = Screen.TODAY_STOPS },
                    onLoginClick = { code, user, pass ->
                        isLoading = true
                        errorMessage = null
                        lifecycleScope.launch {
                            try {
                                val res = RetrofitClient.apiService.login(
                                    LoginRequest(businessCode = code, username = user, password = pass)
                                )
                                if (res.isSuccessful && res.body() != null) {
                                    val authRes = res.body()!!
                                    RetrofitClient.setAuthToken(authRes.accessToken)
                                    authUser = authRes.user
                                    currentScreen = Screen.TODAY_STOPS
                                    refreshStops()
                                } else {
                                    errorMessage = "Invalid credentials. Please verify your business code and username."
                                }
                            } catch (e: Exception) {
                                errorMessage = "Connection error: ${e.localizedMessage}"
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    errorMessage = errorMessage,
                    isLoading = isLoading
                )
            }

            Screen.TODAY_STOPS -> {
                TodayStopsScreen(
                    stops = stops,
                    isLoading = isLoading,
                    onShopClick = { stopItem ->
                        selectedShop = stopItem.shop
                        // Perform location check-in
                        isLoading = true
                        lifecycleScope.launch {
                            try {
                                val fixRes = locationHelper.getFreshLocationFix()
                                if (fixRes.isSuccess) {
                                    val fix = fixRes.getOrThrow()
                                    val checkinRes = RetrofitClient.apiService.checkIn(
                                        CheckInRequest(
                                            shopId = stopItem.shop.id,
                                            lat = fix.lat,
                                            lng = fix.lng,
                                            accuracyMeters = fix.accuracyMeters,
                                            fixAgeSeconds = fix.fixAgeSeconds,
                                            isMock = fix.isMock
                                        )
                                    )
                                    if (checkinRes.isSuccessful && checkinRes.body() != null) {
                                        currentVisitId = checkinRes.body()!!.visitId
                                        currentGrantId = checkinRes.body()!!.grantId
                                        currentScreen = Screen.VISIT_OUTCOME
                                    } else {
                                        val errBody = checkinRes.errorBody()?.string()
                                        Toast.makeText(this@MainActivity, "Check-in blocked: $errBody", Toast.LENGTH_LONG).show()
                                    }
                                } else {
                                    Toast.makeText(this@MainActivity, "GPS Fix Error: Please move outside for clear sky view.", Toast.LENGTH_LONG).show()
                                }
                            } catch (e: Exception) {
                                Toast.makeText(this@MainActivity, "Error during check-in: ${e.message}", Toast.LENGTH_SHORT).show()
                            } finally {
                                isLoading = false
                            }
                        }
                    },
                    onRefresh = { refreshStops() }
                )
            }

            Screen.VISIT_OUTCOME -> {
                selectedShop?.let { shop ->
                    VisitOutcomeScreen(
                        shop = shop,
                        isSubmitting = isLoading,
                        errorMessage = errorMessage,
                        onSubmitClick = { outcome, reason, notes ->
                            if (outcome == "order_placed") {
                                currentScreen = Screen.ORDER_FORM
                            } else {
                                isLoading = true
                                errorMessage = null
                                lifecycleScope.launch {
                                    try {
                                        val fixRes = locationHelper.getFreshLocationFix()
                                        if (fixRes.isSuccess && currentVisitId != null && currentGrantId != null) {
                                            val fix = fixRes.getOrThrow()
                                            val subRes = RetrofitClient.apiService.submitVisit(
                                                VisitSubmitRequest(
                                                    visitId = currentVisitId!!,
                                                    grantId = currentGrantId!!,
                                                    outcome = outcome,
                                                    noOrderReason = reason,
                                                    notes = notes,
                                                    lat = fix.lat,
                                                    lng = fix.lng,
                                                    accuracyMeters = fix.accuracyMeters,
                                                    fixAgeSeconds = fix.fixAgeSeconds,
                                                    isMock = fix.isMock,
                                                    idempotencyKey = UUID.randomUUID().toString()
                                                )
                                            )
                                            if (subRes.isSuccessful) {
                                                Toast.makeText(this@MainActivity, "Visit verified & submitted successfully!", Toast.LENGTH_SHORT).show()
                                                currentScreen = Screen.TODAY_STOPS
                                                refreshStops()
                                            } else {
                                                errorMessage = subRes.errorBody()?.string() ?: "Submission failed"
                                            }
                                        }
                                    } catch (e: Exception) {
                                        errorMessage = e.message
                                    } finally {
                                        isLoading = false
                                    }
                                }
                            }
                        }
                    )
                }
            }

            Screen.ORDER_FORM -> {
                selectedShop?.let { shop ->
                    val sampleCatalog = listOf(
                        CatalogItem("1", "Tapal Danedar Tea 400g", "TAPAL-400G", "pack", 650.0),
                        CatalogItem("2", "National Tomato Ketchup 800g", "NAT-KETCH-800", "piece", 420.0),
                        CatalogItem("3", "Shan Biryani Masala 50g", "SHAN-BIRY-50", "carton", 2400.0)
                    )
                    OrderFormScreen(
                        shop = shop,
                        catalogItems = sampleCatalog,
                        isSubmitting = isLoading,
                        errorMessage = errorMessage,
                        onSubmitOrder = { lines, notes, isUrgent ->
                            isLoading = true
                            lifecycleScope.launch {
                                try {
                                    val fixRes = locationHelper.getFreshLocationFix()
                                    if (fixRes.isSuccess && currentVisitId != null && currentGrantId != null) {
                                        val fix = fixRes.getOrThrow()
                                        val subRes = RetrofitClient.apiService.submitVisit(
                                            VisitSubmitRequest(
                                                visitId = currentVisitId!!,
                                                grantId = currentGrantId!!,
                                                outcome = "order_placed",
                                                notes = notes,
                                                lat = fix.lat,
                                                lng = fix.lng,
                                                accuracyMeters = fix.accuracyMeters,
                                                fixAgeSeconds = fix.fixAgeSeconds,
                                                isMock = fix.isMock,
                                                idempotencyKey = UUID.randomUUID().toString(),
                                                orderLines = lines
                                            )
                                        )
                                        if (subRes.isSuccessful) {
                                            Toast.makeText(this@MainActivity, "Order placed & verified!", Toast.LENGTH_SHORT).show()
                                            currentScreen = Screen.TODAY_STOPS
                                            refreshStops()
                                        } else {
                                            errorMessage = subRes.errorBody()?.string()
                                        }
                                    }
                                } catch (e: Exception) {
                                    errorMessage = e.message
                                } finally {
                                    isLoading = false
                                }
                            }
                        }
                    )
                }
            }
        }
    }
}

