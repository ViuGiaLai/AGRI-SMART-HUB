# -*- coding: utf-8 -*-
# core/report_manager.py
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from tkinter import filedialog, messagebox
import os
import customtkinter as ctk
from database.db_manager import DatabaseManager

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class ReportManager:
    """Quản lý xuất báo cáo Excel và PDF"""

    def __init__(self, db_manager: DatabaseManager, user_id: str):
        self.db = db_manager
        self.user_id = user_id

    # ──────────────────────────────────────────────
    # 1. BÁO CÁO GIAO DỊCH
    # ──────────────────────────────────────────────
    def export_transactions_to_excel(self, start_date: str = None, end_date: str = None):
        """Xuất báo cáo giao dịch ra Excel"""
        try:
            transactions = self.db.get_transactions(self.user_id, start_date, end_date)

            if not transactions:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu giao dịch để xuất!")
                return None

            data = []
            for trans in transactions:
                data.append({
                    "Ngày giao dịch": self.format_date(trans.get('created_at')),
                    "Nông dân": trans.get('farmers', {}).get('name', 'N/A'),
                    "Sản phẩm": trans.get('products', {}).get('name', 'N/A'),
                    "Tổng cân (kg)": trans.get('gross_weight', 0),
                    "Bao bì (kg)": trans.get('package_weight', 0),
                    "Độ ẩm (%)": trans.get('measured_moisture', 0),
                    "Tạp chất (%)": trans.get('measured_impurity', 0),
                    "Cân tịnh (kg)": trans.get('net_weight', 0),
                    "Đơn giá (VNĐ/kg)": trans.get('unit_price', 0),
                    "Thành tiền (VNĐ)": trans.get('total_amount', 0),
                    "Thanh toán": "Đã trả" if trans.get('payment_status') == 'paid' else "Ghi nợ",
                })

            df = pd.DataFrame(data)
            total_amount = df["Thành tiền (VNĐ)"].sum()
            total_weight = df["Cân tịnh (kg)"].sum()

            summary_df = pd.DataFrame([{
                "Ngày giao dịch": "TỔNG CỘNG",
                "Nông dân": "", "Sản phẩm": "", "Tổng cân (kg)": "",
                "Bao bì (kg)": "", "Độ ẩm (%)": "", "Tạp chất (%)": "",
                "Cân tịnh (kg)": f"{total_weight:,.1f}",
                "Đơn giá (VNĐ/kg)": "",
                "Thành tiền (VNĐ)": f"{total_amount:,.0f}",
                "Thanh toán": "",
            }])
            df = pd.concat([df, summary_df], ignore_index=True)

            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"bao_cao_giao_dich_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )
            if not filename:
                return None

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Giao dịch", index=False)
                worksheet = writer.sheets["Giao dịch"]
                for column in worksheet.columns:
                    max_length = max(
                        (len(str(cell.value)) for cell in column if cell.value), default=0
                    )
                    worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 30)

            messagebox.showinfo("Thành công", f"Đã xuất báo cáo:\n{os.path.basename(filename)}")
            return filename

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất Excel giao dịch: {e}")
            return None

    # ──────────────────────────────────────────────
    # 2. BÁO CÁO DOANH THU (method mới — report_frame gọi)
    # ──────────────────────────────────────────────
    def export_revenue_report(self, start_date: str = None, end_date: str = None):
        """Xuất báo cáo doanh thu theo sản phẩm và theo tháng ra Excel"""
        try:
            transactions = self.db.get_transactions(self.user_id, start_date, end_date)

            if not transactions:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất báo cáo doanh thu!")
                return None

            # Tổng hợp theo sản phẩm
            by_product: dict = {}
            by_month: dict = {}

            for t in transactions:
                product = t.get('products', {}).get('name', 'Khác')
                amount = float(t.get('total_amount') or 0)
                weight = float(t.get('net_weight') or 0)
                date_str = str(t.get('created_at', ''))[:7]  # YYYY-MM

                # Theo sản phẩm
                if product not in by_product:
                    by_product[product] = {'so_giao_dich': 0, 'tong_kg': 0.0, 'tong_vnd': 0.0}
                by_product[product]['so_giao_dich'] += 1
                by_product[product]['tong_kg'] += weight
                by_product[product]['tong_vnd'] += amount

                # Theo tháng
                if date_str not in by_month:
                    by_month[date_str] = {'so_giao_dich': 0, 'tong_kg': 0.0, 'tong_vnd': 0.0}
                by_month[date_str]['so_giao_dich'] += 1
                by_month[date_str]['tong_kg'] += weight
                by_month[date_str]['tong_vnd'] += amount

            df_product = pd.DataFrame([
                {
                    "Sản phẩm": k,
                    "Số giao dịch": v['so_giao_dich'],
                    "Tổng cân tịnh (kg)": round(v['tong_kg'], 2),
                    "Tổng doanh thu (VNĐ)": round(v['tong_vnd'], 0),
                }
                for k, v in by_product.items()
            ])

            df_month = pd.DataFrame([
                {
                    "Tháng": k,
                    "Số giao dịch": v['so_giao_dich'],
                    "Tổng cân tịnh (kg)": round(v['tong_kg'], 2),
                    "Tổng doanh thu (VNĐ)": round(v['tong_vnd'], 0),
                }
                for k, v in sorted(by_month.items())
            ])

            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"bao_cao_doanh_thu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )
            if not filename:
                return None

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df_product.to_excel(writer, sheet_name="Theo sản phẩm", index=False)
                df_month.to_excel(writer, sheet_name="Theo tháng", index=False)
                for sheet_name in writer.sheets:
                    ws = writer.sheets[sheet_name]
                    for col in ws.columns:
                        max_len = max((len(str(c.value)) for c in col if c.value), default=0)
                        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 30)

            messagebox.showinfo("Thành công", f"Đã xuất báo cáo doanh thu:\n{os.path.basename(filename)}")
            return filename

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất Excel doanh thu: {e}")
            return None

    # ──────────────────────────────────────────────
    # 3. BÁO CÁO NÔNG DÂN (method mới — report_frame gọi)
    # ──────────────────────────────────────────────
    def export_farmers_to_excel(self):
        """Xuất danh sách nông dân kèm công nợ ra Excel"""
        try:
            farmers = self.db.get_farmers(self.user_id)

            if not farmers:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu nông dân để xuất!")
                return None

            data = []
            total_debt = 0

            for i, farmer in enumerate(farmers, 1):
                debt = float(farmer.get('total_debt') or 0)
                total_debt += debt
                data.append({
                    "STT": i,
                    "Tên nông dân": farmer.get('name', ''),
                    "Số điện thoại": farmer.get('phone', ''),
                    "Địa chỉ": farmer.get('address', ''),
                    "Công nợ hiện tại (VNĐ)": debt,
                    "Ngày tạo": self.format_date(farmer.get('created_at')),
                    "Ghi chú": farmer.get('note', ''),
                })

            # Dòng tổng
            data.append({
                "STT": "TỔNG",
                "Tên nông dân": f"{len(farmers)} nông dân",
                "Số điện thoại": "", "Địa chỉ": "",
                "Công nợ hiện tại (VNĐ)": total_debt,
                "Ngày tạo": "", "Ghi chú": "",
            })

            df = pd.DataFrame(data)

            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"bao_cao_nong_dan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )
            if not filename:
                return None

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Nông dân", index=False)
                ws = writer.sheets["Nông dân"]
                for col in ws.columns:
                    max_len = max((len(str(c.value)) for c in col if c.value), default=0)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 30)

            messagebox.showinfo("Thành công", f"Đã xuất danh sách nông dân:\n{os.path.basename(filename)}")
            return filename

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất Excel nông dân: {e}")
            return None

    # ──────────────────────────────────────────────
    # 4. BÁO CÁO SẢN PHẨM / TỒN KHO (method mới — report_frame gọi)
    # ──────────────────────────────────────────────
    def export_products_to_excel(self):
        """Xuất báo cáo sản phẩm và tồn kho ra Excel"""
        try:
            inventory = self.db.get_inventory(self.user_id)

            if not inventory:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu tồn kho để xuất!")
                return None

            data = []
            total_stock = 0.0

            for i, inv in enumerate(inventory, 1):
                product_name = inv.get('products', {}).get('name', 'N/A')
                stock = float(inv.get('current_stock') or 0)
                total_stock += stock
                data.append({
                    "STT": i,
                    "Sản phẩm": product_name,
                    "Tồn kho (kg)": stock,
                    "Đơn vị": "kg",
                    "Cập nhật lần cuối": self.format_date(inv.get('last_updated')),
                })

            # Dòng tổng
            data.append({
                "STT": "TỔNG",
                "Sản phẩm": f"{len(inventory)} sản phẩm",
                "Tồn kho (kg)": round(total_stock, 2),
                "Đơn vị": "kg",
                "Cập nhật lần cuối": "",
            })

            df = pd.DataFrame(data)

            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"bao_cao_san_pham_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )
            if not filename:
                return None

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Tồn kho", index=False)
                ws = writer.sheets["Tồn kho"]
                for col in ws.columns:
                    max_len = max((len(str(c.value)) for c in col if c.value), default=0)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 30)

            messagebox.showinfo("Thành công", f"Đã xuất báo cáo sản phẩm:\n{os.path.basename(filename)}")
            return filename

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất Excel sản phẩm: {e}")
            return None

    # ──────────────────────────────────────────────
    # 5. BÁO CÁO CÔNG NỢ (giữ nguyên tên cũ để không break code khác)
    # ──────────────────────────────────────────────
    def export_farmer_debt_to_excel(self):
        """Alias gọi export_farmers_to_excel (tương thích ngược)"""
        return self.export_farmers_to_excel()

    def export_inventory_to_excel(self):
        """Alias gọi export_products_to_excel (tương thích ngược)"""
        return self.export_products_to_excel()

    # ──────────────────────────────────────────────
    # 6. XUẤT PDF TỔNG HỢP
    # ──────────────────────────────────────────────
    def export_full_report_to_pdf(self):
        """Xuất báo cáo tổng hợp ra PDF"""
        if not PDF_SUPPORT:
            messagebox.showerror(
                "Lỗi",
                "Chưa cài đặt thư viện reportlab!\nVui lòng chạy: pip install reportlab",
            )
            return None

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"bao_cao_tong_hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
            if not filename:
                return None

            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'CustomTitle', parent=styles['Heading1'],
                fontSize=20, textColor=colors.HexColor('#27ae60'),
                alignment=1, spaceAfter=20,
            )
            story.append(Paragraph("HỆ THỐNG GASH - GIA LAI AGRI-SMART HUB", title_style))

            info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
            story.append(Paragraph(
                f"Ngày báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>"
                f"Mã đại lý: {self.user_id[:8]}...",
                info_style,
            ))
            story.append(Spacer(1, 20))

            stats = self.db.get_dashboard_stats(self.user_id)
            stats_data = [
                ["THỐNG KÊ TỔNG HỢP", ""],
                ["Tổng số nông dân", str(stats.get('total_farmers', 0))],
                ["Tổng số giao dịch", str(stats.get('total_transactions', 0))],
                ["Tổng khối lượng thu mua", f"{stats.get('total_weight', 0):,.1f} kg"],
                ["Tổng doanh thu", f"{stats.get('total_value', 0):,.0f} VNĐ"],
                ["Tổng tồn kho", f"{stats.get('total_stock', 0):,.1f} kg"],
            ]

            stats_table = Table(stats_data, colWidths=[200, 150])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(stats_table)

            doc.build(story)
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo PDF:\n{os.path.basename(filename)}")
            return filename

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất PDF: {e}")
            return None

    # ──────────────────────────────────────────────
    # HELPER
    # ──────────────────────────────────────────────
    def format_date(self, date_value):
        if not date_value:
            return ""
        try:
            if isinstance(date_value, str):
                dt = (
                    datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    if 'T' in date_value
                    else datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
                )
                return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass
        return str(date_value)[:16]