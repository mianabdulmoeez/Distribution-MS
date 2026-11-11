package com.dms.app.data.model

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    @SerializedName("business_code") val businessCode: String,
    @SerializedName("username") val username: String,
    @SerializedName("password") val password: String,
    @SerializedName("device_info") val deviceInfo: String? = null
)

data class AuthUser(
    val id: String,
    @SerializedName("full_name") val fullName: String,
    val username: String,
    val role: String,
    @SerializedName("tenant_id") val tenantId: String,
    @SerializedName("business_name") val businessName: String,
    @SerializedName("business_code") val businessCode: String
)

data class AuthResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("refresh_token") val refreshToken: String,
    @SerializedName("token_type") val tokenType: String,
    val user: AuthUser
)

data class Shop(
    val id: String,
    val name: String,
    @SerializedName("area_id") val areaId: String,
    val address: String,
    val landmark: String?,
    val city: String,
    @SerializedName("contact_person") val contactPerson: String?,
    @SerializedName("contact_phone") val contactPhone: String?,
    @SerializedName("entrance_lat") val entranceLat: Double,
    @SerializedName("entrance_lng") val entranceLng: Double,
    @SerializedName("entrance_pin") val entrancePin: String,
    @SerializedName("radius_meters") val radiusMeters: Double
)

data class TodayShopItem(
    @SerializedName("stop_id") val stopId: String,
    @SerializedName("sequence_order") val sequenceOrder: Int,
    val status: String,
    val shop: Shop
)

data class CheckInRequest(
    @SerializedName("shop_id") val shopId: String,
    val lat: Double,
    val lng: Double,
    @SerializedName("accuracy_meters") val accuracyMeters: Float,
    @SerializedName("fix_age_seconds") val fixAgeSeconds: Float,
    @SerializedName("is_mock") val isMock: Boolean,
    @SerializedName("device_monotonic_time") val deviceMonotonicTime: Long? = null
)

data class CheckInResponse(
    @SerializedName("visit_id") val visitId: String,
    @SerializedName("grant_id") val grantId: String,
    @SerializedName("challenge_token") val challengeToken: String,
    @SerializedName("grant_expires_at") val grantExpiresAt: String,
    @SerializedName("distance_meters") val distanceMeters: Float,
    val message: String
)

data class OrderLineInput(
    @SerializedName("product_id") val productId: String,
    @SerializedName("qty_requested") val qtyRequested: Int
)

data class CustomRequestInput(
    @SerializedName("item_description") val itemDescription: String,
    val quantity: String? = null,
    val requirements: String? = null,
    val priority: String = "normal",
    @SerializedName("callback_phone") val callbackPhone: String? = null
)

data class VisitSubmitRequest(
    @SerializedName("visit_id") val visitId: String,
    @SerializedName("grant_id") val grantId: String,
    val outcome: String,
    @SerializedName("no_order_reason") val noOrderReason: String? = null,
    val notes: String? = null,
    val lat: Double,
    val lng: Double,
    @SerializedName("accuracy_meters") val accuracyMeters: Float,
    @SerializedName("fix_age_seconds") val fixAgeSeconds: Float,
    @SerializedName("is_mock") val isMock: Boolean,
    @SerializedName("idempotency_key") val idempotencyKey: String,
    @SerializedName("order_lines") val orderLines: List<OrderLineInput> = emptyList(),
    @SerializedName("custom_request") val customRequest: CustomRequestInput? = null
)

data class VisitSubmitResponse(
    val message: String,
    @SerializedName("order_id") val orderId: String? = null,
    @SerializedName("custom_request_id") val customRequestId: String? = null
)

