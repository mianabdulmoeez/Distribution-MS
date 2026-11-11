package com.dms.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.dms.app.data.model.OrderLineInput
import com.dms.app.data.model.Shop

data class CatalogItem(
    val id: String,
    val name: String,
    val sku: String,
    val unit: String,
    val pricePkr: Double
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderFormScreen(
    shop: Shop,
    catalogItems: List<CatalogItem>,
    isSubmitting: Boolean,
    errorMessage: String?,
    onSubmitOrder: (lines: List<OrderLineInput>, notes: String, isUrgent: Boolean) -> Unit
) {
    val selectedQuantities = remember { mutableStateMapOf<String, Int>() }
    var notes by remember { mutableStateOf("") }
    var isUrgent by remember { mutableStateOf(false) }

    val orderTotal = catalogItems.sumOf { item ->
        val qty = selectedQuantities[item.id] ?: 0
        qty * item.pricePkr
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Catalog Order Entry") },
                subtitle = { Text(shop.name) }
            )
        },
        bottomBar = {
            Surface(
                tonalElevation = 8.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = "Order Total:", style = MaterialTheme.typography.titleMedium)
                        Text(
                            text = "Rs. ${"%,.2f".format(orderTotal)}",
                            style = MaterialTheme.typography.titleLarge,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = {
                            val lines = selectedQuantities.filter { it.value > 0 }.map {
                                OrderLineInput(productId = it.key, qtyRequested = it.value)
                            }
                            onSubmitOrder(lines, notes, isUrgent)
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(50.dp),
                        enabled = !isSubmitting && orderTotal > 0
                    ) {
                        if (isSubmitting) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                        } else {
                            Text("Submit Order (${selectedQuantities.count { it.value > 0 }} items)")
                        }
                    }
                }
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Checkbox(
                        checked = isUrgent,
                        onCheckedChange = { isUrgent = it }
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(text = "Mark as Urgent Delivery", style = MaterialTheme.typography.bodyMedium)
                }
            }

            items(catalogItems) { item ->
                val currentQty = selectedQuantities[item.id] ?: 0
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(text = item.name, style = MaterialTheme.typography.titleSmall)
                            Text(
                                text = "SKU: ${item.sku} • Unit: ${item.unit}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                text = "Rs. ${item.pricePkr}",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }

                        Row(verticalAlignment = Alignment.CenterVertically) {
                            FilledTonalButton(
                                onClick = {
                                    if (currentQty > 0) selectedQuantities[item.id] = currentQty - 1
                                },
                                contentPadding = PaddingValues(horizontal = 12.dp)
                            ) {
                                Text("-")
                            }

                            Text(
                                text = "$currentQty",
                                modifier = Modifier.padding(horizontal = 12.dp),
                                style = MaterialTheme.typography.titleMedium
                            )

                            FilledTonalButton(
                                onClick = {
                                    selectedQuantities[item.id] = currentQty + 1
                                },
                                contentPadding = PaddingValues(horizontal = 12.dp)
                            ) {
                                Text("+")
                            }
                        }
                    }
                }
            }

            item {
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Order Notes (Optional)") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2
                )
            }

            if (!errorMessage.isNullOrEmpty()) {
                item {
                    Text(
                        text = errorMessage,
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
    }
}

