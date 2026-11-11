package com.dms.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.dms.app.data.model.Shop

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VisitOutcomeScreen(
    shop: Shop,
    isSubmitting: Boolean,
    errorMessage: String?,
    onSubmitClick: (outcome: String, noOrderReason: String?, notes: String) -> Unit
) {
    val outcomes = listOf(
        "no_order" to "No Order",
        "order_placed" to "Order Placed",
        "shop_closed" to "Shop Closed",
        "contact_unavailable" to "Contact Unavailable"
    )

    val noOrderReasons = listOf(
        "sufficient_stock" to "Sufficient Stock",
        "price_objection" to "Price Objection",
        "credit_issue" to "Payment / Credit Issue",
        "other" to "Other"
    )

    var selectedOutcome by remember { mutableStateOf("no_order") }
    var selectedReason by remember { mutableStateOf("sufficient_stock") }
    var notes by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Record Visit Outcome") },
                subtitle = { Text(shop.name) }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(text = "Location Verified", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                    Text(text = "Checked in at: ${shop.address}", style = MaterialTheme.typography.bodySmall)
                    Text(text = "Entrance PIN: ${shop.entrancePin}", style = MaterialTheme.typography.bodySmall)
                }
            }

            Text(text = "Select Outcome:", style = MaterialTheme.typography.titleMedium)

            Column(Modifier.selectableGroup()) {
                outcomes.forEach { (key, label) ->
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                            .selectable(
                                selected = (selectedOutcome == key),
                                onClick = { selectedOutcome = key },
                                role = Role.RadioButton
                            ),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = (selectedOutcome == key),
                            onClick = null
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(text = label, style = MaterialTheme.typography.bodyLarge)
                    }
                }
            }

            if (selectedOutcome == "no_order") {
                Text(text = "Required Reason for No Order:", style = MaterialTheme.typography.titleSmall)
                Column(Modifier.selectableGroup()) {
                    noOrderReasons.forEach { (key, label) ->
                        Row(
                            Modifier
                                .fillMaxWidth()
                                .height(40.dp)
                                .selectable(
                                    selected = (selectedReason == key),
                                    onClick = { selectedReason = key },
                                    role = Role.RadioButton
                                ),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = (selectedReason == key),
                                onClick = null
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(text = label, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }

            OutlinedTextField(
                value = notes,
                onValueChange = { notes = it },
                label = { Text("Visit Notes (Optional)") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3
            )

            if (!errorMessage.isNullOrEmpty()) {
                Text(
                    text = errorMessage,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            Button(
                onClick = {
                    onSubmitClick(
                        selectedOutcome,
                        if (selectedOutcome == "no_order") selectedReason else null,
                        notes
                    )
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                enabled = !isSubmitting
            ) {
                if (isSubmitting) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                } else {
                    Text("Submit Verified Outcome")
                }
            }
        }
    }
}

