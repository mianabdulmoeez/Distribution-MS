export interface User {
  id: string;
  full_name: string;
  username?: string;
  role: string;
  tenant_id?: string;
  business_name?: string;
  business_code?: string;
  is_platform_admin?: boolean;
}

export interface Area {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Shop {
  id: string;
  name: string;
  area_id: string;
  address: string;
  landmark?: string;
  city: string;
  contact_person?: string;
  contact_phone?: string;
  entrance_lat: number;
  entrance_lng: number;
  entrance_pin: string;
  status: "pending" | "approved" | "rejected" | "archived";
  radius_meters: number;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  unit: string;
  price_pkr: number;
  is_active: boolean;
}

export interface Order {
  id: string;
  shop_name: string;
  shop_address: string;
  origin: "field" | "office";
  status: "submitted" | "confirmed" | "dispatched" | "delivered" | "delivery_failed" | "rejected" | "cancelled";
  total_amount: number;
  confirmed_amount?: number;
  is_urgent: boolean;
  created_at: string;
}

export interface DashboardSummary {
  service_date: string;
  planned_coverage: {
    total_stops: number;
    completed_stops: number;
    coverage_percentage: number;
  };
  visits: {
    total_verified: number;
    order_placed: number;
    no_order: number;
    other_outcomes: number;
  };
  orders_pending_confirmation: number;
}

