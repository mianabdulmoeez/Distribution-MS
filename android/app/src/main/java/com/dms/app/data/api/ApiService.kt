package com.dms.app.data.api

import com.dms.app.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    @POST("auth/login")
    async suspend fun login(
        @Body request: LoginRequest
    ): Response<AuthResponse>

    @GET("field/today")
    suspend fun getTodayStops(): Response<List<TodayShopItem>>

    @GET("field/shops")
    suspend fun getAssignedShops(): Response<List<Shop>>

    @POST("field/check-in")
    suspend fun checkIn(
        @Body request: CheckInRequest
    ): Response<CheckInResponse>

    @POST("field/submit")
    suspend fun submitVisit(
        @Body request: VisitSubmitRequest
    ): Response<VisitSubmitResponse>
}

