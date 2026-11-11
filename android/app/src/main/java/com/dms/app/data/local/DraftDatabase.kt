package com.dms.app.data.local

import androidx.room.*

@Entity(tableName = "draft_visits")
data class DraftVisitEntity(
    @PrimaryKey val id: String,
    val shopId: String,
    val shopName: String,
    val outcome: String,
    val noOrderReason: String?,
    val notes: String?,
    val idempotencyKey: String,
    val createdAt: Long = System.currentTimeMillis()
)

@Dao
interface DraftVisitDao {
    @Query("SELECT * FROM draft_visits ORDER BY createdAt DESC")
    suspend fun getAllDrafts(): List<DraftVisitEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun saveDraft(draft: DraftVisitEntity)

    @Query("DELETE FROM draft_visits WHERE id = :id")
    suspend fun deleteDraft(id: String)

    @Query("DELETE FROM draft_visits")
    suspend fun clearAllDrafts()
}

@Database(entities = [DraftVisitEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun draftVisitDao(): DraftVisitDao
}

