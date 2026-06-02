# -*- coding: utf-8 -*-
"""Hệ thống cảnh báo thông minh — giám sát giá, tồn kho, công nợ."""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import customtkinter as ctk

from database.db_manager import DatabaseManager
from ui import theme as T

logger = logging.getLogger(__name__)

AlertItem = Tuple[str, str, str]  # (level_label, message, alert_type)


def _widget_alive(widget) -> bool:
    """Kiểm tra widget Tk còn tồn tại (tránh TclError sau khi destroy)."""
    if widget is None:
        return False
    try:
        return bool(widget.winfo_exists())
    except Exception:
        return False


class NotificationSystem:
    """Giám sát nền và popup cảnh báo cho đại lý."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        user_id: str,
        parent_widget=None,
        root_window=None,
    ):
        self.db = db_manager
        self.user_id = user_id
        self.parent_widget = parent_widget
        self.root_window = root_window or (
            parent_widget.winfo_toplevel() if _widget_alive(parent_widget) else None
        )
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_check: dict = {}
        self._pending_after_ids: list = []
        self._open_popups: list = []
        self.alert_widget: Optional["AlertWidget"] = None
        self.thresholds = {
            "price_change_percent": 5,
            "low_stock": 100,
            "high_stock": 5000,
            "high_debt": 100_000_000,
            "farmer_debt": 10_000_000,
        }

    def start_monitoring(self, interval_seconds: int = 300):
        if self.is_running:
            return
        self.is_running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval_seconds,), daemon=True
        )
        self.monitor_thread.start()
        logger.info("Notification system started")

    def stop_monitoring(self):
        self.is_running = False

        if self.alert_widget is not None:
            self.alert_widget.cancel_refresh()

        if _widget_alive(self.root_window):
            for aid in self._pending_after_ids:
                try:
                    self.root_window.after_cancel(aid)
                except Exception:
                    pass
        self._pending_after_ids.clear()

        for popup in list(self._open_popups):
            try:
                if _widget_alive(popup):
                    popup.destroy()
            except Exception:
                pass
        self._open_popups.clear()

        logger.info("Notification system stopped")

    def _monitor_loop(self, interval_seconds: int):
        while self.is_running:
            try:
                if not self.is_running:
                    break
                self.check_price_alerts()
                if not self.is_running:
                    break
                self.check_inventory_alerts()
                if not self.is_running:
                    break
                self.check_debt_alerts()
            except Exception as e:
                logger.error("Monitor loop error: %s", e)
            # Ngủ từng giây để stop_monitoring phản hồi nhanh
            for _ in range(interval_seconds):
                if not self.is_running:
                    break
                time.sleep(1)

    def _cooldown_elapsed(self, key: str, seconds: int) -> bool:
        last = self.last_check.get(key)
        if not last:
            return True
        return (datetime.now() - last).total_seconds() >= seconds

    def check_price_alerts(self):
        if not self.is_running:
            return
        try:
            for product in ("Cà phê", "Hồ tiêu"):
                prices = self.db.get_market_prices(product, days=2)
                if len(prices) < 2:
                    continue
                cur = prices[0].get("price_local", 0) or 0
                prev = prices[1].get("price_local", 0) or 0
                if prev <= 0:
                    continue
                pct = abs((cur - prev) / prev * 100)
                if pct < self.thresholds["price_change_percent"]:
                    continue
                key = f"price_{product}_{prices[0].get('log_date')}"
                if not self._cooldown_elapsed(key, 3600):
                    continue
                direction = "tăng" if cur > prev else "giảm"
                msg = (
                    f"{product} {direction} {pct:.1f}%\n"
                    f"Hiện tại: {cur:,.0f} VNĐ/kg · Trước: {prev:,.0f} VNĐ/kg"
                )
                self.show_notification("Biến động giá mạnh", msg, "warning")
                self.last_check[key] = datetime.now()
        except Exception as e:
            logger.error("Price alert error: %s", e)

    def check_inventory_alerts(self):
        if not self.is_running:
            return
        try:
            for item in self.db.get_inventory(self.user_id):
                name = item.get("products", {}).get("name", "N/A")
                stock = item.get("current_stock", 0) or 0
                if stock == 0:
                    key = f"out_{name}"
                    if self._cooldown_elapsed(key, 3600):
                        self.show_notification(
                            "Hết hàng",
                            f"{name} đã hết hàng trong kho!\nNhập khẩn cấp để không mất khách.",
                            "danger",
                        )
                        self.last_check[key] = datetime.now()
                elif 0 < stock <= self.thresholds["low_stock"]:
                    key = f"low_{name}"
                    if self._cooldown_elapsed(key, 3600):
                        self.show_notification(
                            "Tồn kho thấp",
                            f"{name}: còn {stock:.1f} kg (< {self.thresholds['low_stock']} kg).",
                            "warning",
                        )
                        self.last_check[key] = datetime.now()
                elif stock >= self.thresholds["high_stock"]:
                    key = f"high_{name}"
                    if self._cooldown_elapsed(key, 86400):
                        self.show_notification(
                            "Tồn kho cao",
                            f"{name}: {stock:.1f} kg — cân nhắc bán bớt.",
                            "info",
                        )
                        self.last_check[key] = datetime.now()
        except Exception as e:
            logger.error("Inventory alert error: %s", e)

    def check_debt_alerts(self):
        if not self.is_running:
            return
        try:
            farmers = self.db.get_farmers(self.user_id)
            total = sum(f.get("total_debt", 0) or 0 for f in farmers)
            if total > self.thresholds["high_debt"] and self._cooldown_elapsed("total_debt", 86400):
                self.show_notification(
                    "Công nợ cao",
                    f"Tổng công nợ: {total:,.0f} VNĐ.\nĐẩy mạnh thu hồi nợ.",
                    "warning",
                )
                self.last_check["total_debt"] = datetime.now()
            for f in farmers:
                debt = f.get("total_debt", 0) or 0
                if debt <= self.thresholds["farmer_debt"]:
                    continue
                key = f"debt_{f.get('id')}"
                if not self._cooldown_elapsed(key, 86400):
                    continue
                self.show_notification(
                    f"Công nợ — {f.get('name', 'N/A')}",
                    f"{debt:,.0f} VNĐ · {f.get('phone', 'Chưa có SĐT')}",
                    "warning",
                )
                self.last_check[key] = datetime.now()
        except Exception as e:
            logger.error("Debt alert error: %s", e)

    def collect_dashboard_alerts(self) -> List[AlertItem]:
        """Thu thập cảnh báo hiển thị trên Dashboard (không popup)."""
        alerts: List[AlertItem] = []
        try:
            for item in self.db.get_inventory(self.user_id):
                name = item.get("products", {}).get("name", "N/A")
                stock = item.get("current_stock", 0) or 0
                if stock == 0:
                    alerts.append(("🔴 CRITICAL", f"{name} — đã hết hàng", "danger"))
                elif stock <= self.thresholds["low_stock"]:
                    alerts.append(("⚠️ WARNING", f"{name} — tồn thấp: {stock:.1f} kg", "warning"))
                elif stock >= self.thresholds["high_stock"]:
                    alerts.append(("📈 INFO", f"{name} — tồn cao: {stock:,.0f} kg", "info"))

            farmers = self.db.get_farmers(self.user_id)
            total_debt = sum(f.get("total_debt", 0) or 0 for f in farmers)
            if total_debt > self.thresholds["high_debt"]:
                alerts.append((
                    "💰 DEBT",
                    f"Tổng công nợ: {total_debt:,.0f} VNĐ",
                    "warning",
                ))

            prices = self.db.get_market_prices("Cà phê", days=2)
            if len(prices) >= 2:
                cur = prices[0].get("price_local", 0) or 0
                prev = prices[1].get("price_local", 0) or 0
                if prev > 0:
                    pct = abs((cur - prev) / prev * 100)
                    if pct >= self.thresholds["price_change_percent"]:
                        d = "↑" if cur > prev else "↓"
                        alerts.append((
                            "📊 PRICE",
                            f"Giá cà phê {d} {pct:.1f}% ({cur:,.0f} VNĐ/kg)",
                            "warning",
                        ))
        except Exception as e:
            logger.error("collect_dashboard_alerts: %s", e)
        return alerts

    def show_notification(self, title: str, message: str, level: str = "info"):
        if not self.is_running:
            return
        if not _widget_alive(self.root_window):
            logger.info("Notification [%s]: %s", title, message)
            return

        colors = {"danger": T.DANGER, "warning": T.ACCENT, "info": T.INFO}
        icons = {"danger": "🔴", "warning": "🟡", "info": "🔵"}

        def show_popup():
            if not self.is_running or not _widget_alive(self.root_window):
                return
            try:
                popup = ctk.CTkToplevel(self.root_window)
                self._open_popups.append(popup)

                def close_popup():
                    try:
                        if popup in self._open_popups:
                            self._open_popups.remove(popup)
                        if _widget_alive(popup):
                            popup.destroy()
                    except Exception:
                        pass

                popup.protocol("WM_DELETE_WINDOW", close_popup)
                popup.title(f"🔔 {title}")
                popup.geometry("440x240")
                popup.attributes("-topmost", True)
                popup.update_idletasks()
                x = (popup.winfo_screenwidth() - 440) // 2
                y = (popup.winfo_screenheight() - 240) // 2
                popup.geometry(f"+{x}+{y}")

                frame = ctk.CTkFrame(popup, fg_color="transparent")
                frame.pack(fill="both", expand=True, padx=20, pady=20)
                ctk.CTkLabel(
                    frame, text=icons.get(level, "🔵"), font=("Segoe UI Emoji", 40),
                ).pack()
                ctk.CTkLabel(
                    frame, text=title, font=ctk.CTkFont(size=15, weight="bold"),
                    text_color=colors.get(level, T.INFO),
                ).pack(pady=6)
                ctk.CTkLabel(
                    frame, text=message, font=ctk.CTkFont(size=12),
                    justify="left", wraplength=380,
                ).pack(pady=(0, 12))
                ctk.CTkButton(
                    frame, text="Đã hiểu", command=close_popup,
                    fg_color=T.PRIMARY, height=36,
                ).pack(fill="x")
                popup.after(12000, close_popup)
            except Exception as e:
                logger.warning("Không hiển thị popup cảnh báo: %s", e)

        try:
            aid = self.root_window.after(0, show_popup)
            self._pending_after_ids.append(aid)
        except Exception as e:
            logger.warning("Không lên lịch popup: %s", e)


class AlertWidget(ctk.CTkFrame):
    """Panel cảnh báo trên Dashboard."""

    REFRESH_MS = 30_000

    def __init__(self, master, notification_system: NotificationSystem, **kwargs):
        super().__init__(
            master, corner_radius=T.CORNER_RADIUS, fg_color=T.BG_CARD,
            border_width=1, border_color=("#fde8e8", "#4a2020"), **kwargs
        )
        self.notification_system = notification_system
        self._refresh_job = None
        self._setup_ui()
        self.refresh_alerts()

    def cancel_refresh(self):
        if self._refresh_job is not None and _widget_alive(self):
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
        self._refresh_job = None

    def _setup_ui(self):
        hdr = ctk.CTkFrame(self, fg_color=T.DANGER, corner_radius=T.CORNER_RADIUS_SM)
        hdr.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(
            hdr, text="🔔 Cảnh báo hệ thống",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=T.TEXT_ON_DARK,
        ).pack(side="left", padx=12, pady=8)
        self.badge = ctk.CTkLabel(
            hdr, text="0", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=T.TEXT_ON_DARK, text_color=T.DANGER,
            corner_radius=10, width=28, height=22,
        )
        self.badge.pack(side="right", padx=12)

        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent", height=100)
        self.content.pack(fill="x", padx=12, pady=(0, 12))

    def refresh_alerts(self):
        self._refresh_job = None
        if not _widget_alive(self):
            return
        if not self.notification_system.is_running:
            return

        for w in self.content.winfo_children():
            w.destroy()

        alerts = self.notification_system.collect_dashboard_alerts()
        self.badge.configure(text=str(len(alerts)))

        if not alerts:
            ctk.CTkLabel(
                self.content, text="✅ Không có cảnh báo — hệ thống ổn định",
                font=ctk.CTkFont(size=12), text_color=T.PRIMARY,
            ).pack(pady=8)
        else:
            for level, msg, atype in alerts[:8]:
                self._add_row(level, msg, atype)

        if self.notification_system.is_running and _widget_alive(self):
            self._refresh_job = self.after(self.REFRESH_MS, self.refresh_alerts)

    def _add_row(self, level: str, message: str, alert_type: str):
        colors = {"danger": T.DANGER, "warning": T.ACCENT, "info": T.INFO}
        row = ctk.CTkFrame(
            self.content, corner_radius=8, fg_color=("#fafafa", "#333"),
        )
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(
            row, text=level, width=90, font=ctk.CTkFont(size=10, weight="bold"),
            text_color=colors.get(alert_type, T.INFO),
        ).pack(side="left", padx=8, pady=6)
        ctk.CTkLabel(
            row, text=message, font=ctk.CTkFont(size=11),
            anchor="w", wraplength=520,
        ).pack(side="left", fill="x", expand=True, pady=6)
        ctk.CTkLabel(
            row, text=datetime.now().strftime("%H:%M"),
            font=ctk.CTkFont(size=9), text_color=T.TEXT_MUTED,
        ).pack(side="right", padx=8)


def add_alerts_to_dashboard(dashboard_frame, db_manager, user_id, root_window=None):
    """Gắn widget cảnh báo lên Dashboard và bật giám sát nền."""
    root = root_window or dashboard_frame.winfo_toplevel()

    for w in dashboard_frame.alerts_container.winfo_children():
        w.destroy()

    notification_system = NotificationSystem(
        db_manager, user_id, root_window=root,
    )
    alert_widget = AlertWidget(dashboard_frame.alerts_container, notification_system)
    alert_widget.pack(fill="x")
    notification_system.alert_widget = alert_widget
    notification_system.start_monitoring()

    return notification_system
