"""Simulation engine for day advancement."""
from datetime import datetime, timedelta
from typing import List, Dict
import random
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.event import EventLog
from app.models.order import ManufacturingOrder
from app.models.product import ProductModel
from app.models.purchase_order import PurchaseOrder
from app.core.config import get_settings
from app.services.inventory_service import InventoryService


class SimulationEngine:
    """Engine for running simulation day cycles."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.current_day = 1
        self.current_date = datetime.strptime(
            self.settings.SIMULATION_START_DATE, "%Y-%m-%d"
        ).date()

    def advance_day(self) -> Dict:
        """Advance simulation by one day."""
        events = []

        # Step 1: Process arriving POs first
        po_events = self._process_purchase_orders()
        events.extend(po_events)

        # Step 2: Generate new demand
        demand_events = self._generate_demand()
        events.extend(demand_events)

        # Step 3: Process manufacturing orders within capacity
        order_events = self._process_manufacturing_orders()
        events.extend(order_events)

        # Step 4: Take inventory snapshot
        snapshot_event = self._take_inventory_snapshot()
        events.append(snapshot_event)

        # Increment day counter
        previous_day = self.current_day
        self.current_day += 1
        self.current_date += timedelta(days=1)

        return {
            "previous_day": previous_day,
            "new_day": self.current_day,
            "current_date": self.current_date.isoformat(),
            "events_generated": events
        }

    def _process_purchase_orders(self) -> List[Dict]:
        """Process purchase orders due today."""
        events = []

        todays_po = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.expected_delivery <= self.current_date,
            PurchaseOrder.status.in_(["pending", "partial"])
        ).all()

        for po in todays_po:
            # Check if partial delivery (~5-10% chance)
            should_be_partial = random.random() < 0.07  # 7% chance

            if should_be_partial and float(po.quantity_ordered - po.quantity_delivered) > 0:
                # Deliver ~70-90% of remaining
                remaining = float(po.quantity_ordered - po.quantity_delivered)
                actual_delivery = int(remaining * random.uniform(0.70, 0.90))

                inv_svc = InventoryService(self.db)
                inv_svc.adjust(po.product_name, Decimal(str(
                    float(inv_svc.get_by_product(po.product_name).quantity or 0) + actual_delivery
                )))

                po.quantity_delivered += actual_delivery
                po.status = "partial"
                po.actual_delivery = self.current_date

                events.append({
                    "type": "po_partial_delivery",
                    "po_id": po.id,
                    "product": po.product_name,
                    "delivered": actual_delivery,
                    "expected": int(po.quantity_ordered - po.quantity_delivered + actual_delivery)
                })
            else:
                # Full delivery
                remaining = float(po.quantity_ordered - po.quantity_delivered)

                inv_svc = InventoryService(self.db)
                inv_svc.adjust(po.product_name, Decimal(str(
                    float(inv_svc.get_by_product(po.product_name).quantity or 0) + remaining
                )))

                po.quantity_delivered = po.quantity_ordered
                po.status = "delivered"
                po.actual_delivery = self.current_date

                events.append({
                    "type": "po_arrived",
                    "po_id": po.id,
                    "product": po.product_name,
                    "quantity": int(remaining)
                })

        return events

    def _generate_demand(self) -> List[Dict]:
        """Generate new manufacturing orders based on demand parameters."""
        events = []

        # Default demand params (can be configured via API later)
        demand_params = {
            "P3D-Classic": {"mean": 8, "variance": 3},
            "P3D-Pro": {"mean": 5, "variance": 2}
        }

        from app.models.order import ManufacturingOrder

        total_orders = 0
        for model_id, params in demand_params.items():
            # Generate random demand using normal distribution
            mean = params["mean"]
            std_dev = params["variance"]
            quantity = max(0, int(random.gauss(mean, std_dev)))

            if quantity > 0:
                order = ManufacturingOrder(
                    product_model=model_id,
                    quantity_needed=Decimal(str(quantity)),
                    quantity_produced=Decimal("0"),
                    status="pending",
                    created_date=self.current_date
                )
                self.db.add(order)
                total_orders += 1
                events.append({
                    "type": "demand_generated",
                    "model": model_id,
                    "quantity": quantity
                })

        self.db.commit()

        if total_orders > 0:
            events.insert(0, {
                "type": "demand_batch",
                "total_orders": total_orders
            })

        return events

    def _process_manufacturing_orders(self) -> List[Dict]:
        """Process manufacturing orders within daily capacity."""
        events = []
        capacity_per_day = self.settings.DEFAULT_CAPACITY_PER_DAY
        produced_today = 0

        # Get released orders
        released_orders = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.status == "released"
        ).order_by(ManufacturingOrder.created_date.asc()).all()

        for order in released_orders:
            if produced_today >= capacity_per_day:
                break

            # Calculate how much can be produced this day
            remaining_to_produce = float(order.quantity_needed - order.quantity_produced)
            can_produce = min(remaining_to_produce, capacity_per_day - produced_today)

            if can_produce > 0:
                order.quantity_produced += Decimal(str(can_produce))
                produced_today += int(can_produce)

                # Consume materials
                from app.services.inventory_service import InventoryService
                bom_reqs = self.calculate_bom_requirements_for_order(order)
                inv_svc = InventoryService(self.db)

                for material, qty_per_unit in bom_reqs.items():
                    total_consumed = qty_per_unit * can_produce
                    inv_svc.consume(material, Decimal(str(total_consumed)))

                events.append({
                    "type": "material_consumed",
                    "order_id": order.id,
                    "produced": int(can_produce),
                    "materials": bom_reqs
                })

                # Check if order is complete
                if float(order.quantity_produced) >= float(order.quantity_needed):
                    order.status = "completed"
                    order.completed_date = self.current_date
                    events.append({
                        "type": "order_completed",
                        "order_id": order.id,
                        "model": order.product_model,
                        "quantity": int(order.quantity_needed)
                    })

        self.db.commit()

        if produced_today > 0:
            events.insert(0, {
                "type": "production_summary",
                "produced_today": produced_today,
                "capacity_remaining": capacity_per_day - produced_today
            })

        return events

    def calculate_bom_requirements_for_order(self, order: ManufacturingOrder) -> Dict[str, float]:
        """Calculate materials required per unit for an order."""
        bom_items = self.db.query(BOMItem).filter(
            BOMItem.model_id == order.product_model
        ).all()

        return {item.material_name: float(item.quantity_required) for item in bom_items}

    def _take_inventory_snapshot(self) -> Dict:
        """Take daily inventory snapshot."""
        from app.models.inventory import Inventory

        items = self.db.query(Inventory).all()
        snapshot = {}

        for item in items:
            snapshot[item.product_name] = {
                "quantity": float(item.quantity),
                "reserved": float(item.reserved_quantity),
                "available": float(item.quantity - item.reserved_quantity)
            }

        # Log the event
        event = EventLog(
            event_type="inventory_snapshot",
            event_date=self.current_date,
            details=str(snapshot)
        )
        self.db.add(event)
        self.db.commit()

        return {
            "type": "inventory_snapshot",
            "date": self.current_date.isoformat(),
            "item_count": len(items)
        }

    def get_status(self) -> Dict:
        """Get current simulation status."""
        pending_count = self.db.query(ManufacturingOrder).filter(
            ManufacturingOrder.status.in_(["pending", "released"])
        ).count()

        return {
            "current_day": self.current_day,
            "current_date": self.current_date.isoformat(),
            "sim_start_date": self.settings.SIMULATION_START_DATE,
            "pending_orders_count": pending_count,
            "capacity_per_day": self.settings.DEFAULT_CAPACITY_PER_DAY
        }
