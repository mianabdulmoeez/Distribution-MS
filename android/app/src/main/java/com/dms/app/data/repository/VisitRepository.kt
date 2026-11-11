package com.dms.app.data.repository

import com.dms.app.data.api.ApiService
import com.dms.app.data.local.DraftVisitDao
import com.dms.app.data.local.DraftVisitEntity
import com.dms.app.data.model.VisitSubmitRequest
import com.dms.app.data.model.VisitSubmitResponse
import com.dms.app.util.LocationHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.UUID

class VisitRepository(
    private val apiService: ApiService,
    private val draftDao: DraftVisitDao,
    private val locationHelper: LocationHelper
) {

    suspend fun saveDraft(
        shopId: String,
        shopName: String,
        outcome: String,
        noOrderReason: String?,
        notes: String?,
        idempotencyKey: String = UUID.randomUUID().toString()
    ) = withContext(Dispatchers.IO) {
        val draft = DraftVisitEntity(
            id = UUID.randomUUID().toString(),
            shopId = shopId,
            shopName = shopName,
            outcome = outcome,
            noOrderReason = noOrderReason,
            notes = notes,
            idempotencyKey = idempotencyKey
        )
        draftDao.saveDraft(draft)
    }

    suspend fun getDrafts(): List<DraftVisitEntity> = withContext(Dispatchers.IO) {
        draftDao.getAllDrafts()
    }

    suspend fun submitWithFreshLocation(
        visitId: String,
        grantId: String,
        outcome: String,
        noOrderReason: String?,
        notes: String?,
        idempotencyKey: String
    ): Result<VisitSubmitResponse> = withContext(Dispatchers.IO) {
        // Spec Section 04: Require a fresh foreground location check before submission
        val fixResult = locationHelper.getFreshLocationFix()
        if (fixResult.isFailure) {
            return@withContext Result.failure(fixResult.exceptionOrNull() ?: Exception("Failed to get fresh GPS location"))
        }

        val fix = fixResult.getOrThrow()
        val request = VisitSubmitRequest(
            visitId = visitId,
            grantId = grantId,
            outcome = outcome,
            noOrderReason = noOrderReason,
            notes = notes,
            lat = fix.lat,
            lng = fix.lng,
            accuracyMeters = fix.accuracyMeters,
            fixAgeSeconds = fix.fixAgeSeconds,
            isMock = fix.isMock,
            idempotencyKey = idempotencyKey
        )

        try {
            val response = apiService.submitVisit(request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Submission error ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

