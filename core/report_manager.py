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
    
    def export_transactions_to_excel(self, start_date: str = None, end_date: str = None):
        """Xuất báo cáo giao dịch ra Excel"""
        try:
            # Get transactions
            transactions = self.db.get_transactions(self.user_id, start_date, end_date)
            
            if not transactions:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu giao dịch để xuất!")
                return
            
            # Prepare data
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
                    "Thanh toán": "Đã trả" if trans.get('payment_status') == 'paid' else "Ghi nợ"
                })
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Add summary row
            total_amount = df["Thành tiền (VNĐ)"].sum()
            total_weight = df["Cân tịnh (kg)"].sum()
            
            summary_df = pd.DataFrame([{
                "Ngày giao dịch": "TỔNG CỘNG",
                "Nông dân": "",
                "Sản phẩm": "",
                "Tổng cân (kg)": "",
                "Bao bì (kg)": "",
                "Độ ẩm (%)": "",
                "Tạp chất (%)": "",
                "Cân tịnh (kg)": f"{total_weight:,.1f}",
                "Đơn giá (VNĐ/kg)": "",
                "Thành tiền (VNĐ)": f"{total_amount:,.0f}",
                "Thanh toán": ""
            }])
            
            df = pd.concat([df, summary_df], ignore_index=True)
            
            # Save to file
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"bao_cao_giao_dich_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if filename:
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name="Giao dịch", index=False)
                    
                    # Auto-adjust column widths
                    worksheet = writer.sheets["Giao dịch"]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 30)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo ra file:\n{os.path.basename(filename)}")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất Excel: {e}")
    
    def export_farmer_debt_to_excel(self):
        """Xuất báo cáo công nợ nông dân ra Excel"""
        try:
            farmers = self.db.get_farmers(self.user_id)
            
            if not farmers:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu nông dân để xuất!")
                return
            
            # Prepare data
            data = []
            total_debt = 0
            
            for farmer in farmers:
                debt = farmer.get('total_debt', 0)
                total_debt += debt
                
                data.append({
                    "STT": len(data) + 1,
                    "Tên nông dân": farmer.get('name', ''),
                    "Số điện thoại": farmer.get('phone', ''),
                    "Địa chỉ": farmer.get('address', ''),
                    "Công nợ hiện tại (VNĐ)": debt,
                    "Ngày tạo": self.format_date(farmer.get('created_at')),
                    "Ghi chú": farmer.get('note', '')
                })
            
            # Add summary
            data.append({
                "STT": "TỔNG",
                "Tên nông dân": "",
                "Số điện thoại": "",
                "Địa chỉ": "",
                "Công nợ hiện tại (VNĐ)": total_debt,
                "Ngày tạo": "",
                "Ghi chú": ""
            })
            
            df = pd.DataFrame(data)
            
            # Save to file
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"bao_cao_cong_no_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if filename:
                df.to_excel(filename, index=False, sheet_name="Công nợ")
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo công nợ ra file:\n{os.path.basename(filename)}")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất Excel: {e}")
    
    def export_inventory_to_excel(self):
        """Xuất báo cáo tồn kho ra Excel"""
        try:
            inventory = self.db.get_inventory(self.user_id)
            
            if not inventory:
                messagebox.showwarning("Cảnh báo", "Không có dữ liệu tồn kho để xuất!")
                return
            
            data = []
            total_value = 0
            
            for inv in inventory:
                product_name = inv.get('products', {}).get('name', 'N/A')
                stock = inv.get('current_stock', 0)
                estimated_value = stock * 45000  # Giả sử giá 45k/kg
                total_value += estimated_value
                
                data.append({
                    "Sản phẩm": product_name,
                    "Tồn kho (kg)": stock,
                    "Đơn vị": "kg",
                    "Giá trị ước tính (VNĐ)": estimated_value,
                    "Cập nhật lần cuối": self.format_date(inv.get('last_updated'))
                })
            
            # Add summary
            data.append({
                "Sản phẩm": "TỔNG GIÁ TRỊ KHO",
                "Tồn kho (kg)": "",
                "Đơn vị": "",
                "Giá trị ước tính (VNĐ)": total_value,
                "Cập nhật lần cuối": ""
            })
            
            df = pd.DataFrame(data)
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"bao_cao_ton_kho_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if filename:
                df.to_excel(filename, index=False, sheet_name="Tồn kho")
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo tồn kho ra file:\n{os.path.basename(filename)}")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất Excel: {e}")
    
    def export_full_report_to_pdf(self):
        """Xuất báo cáo tổng hợp ra PDF"""
        if not PDF_SUPPORT:
            messagebox.showerror(
                "Lỗi", 
                "Chưa cài đặt thư viện reportlab!\nVui lòng chạy: pip install reportlab"
            )
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"bao_cao_tong_hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not filename:
                return
            
            # Create PDF document
            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2ecc71'),
                alignment=1,
                spaceAfter=30
            )
            
            title = Paragraph("HỆ THỐNG GASH - GIA LAI AGRI-SMART HUB", title_style)
            story.append(title)
            
            # Report info
            info_style = ParagraphStyle(
                'Info',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey
            )
            
            info = Paragraph(f"Ngày báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>"
                           f"Mã đại lý: {self.user_id[:8]}...", info_style)
            story.append(info)
            story.append(Spacer(1, 20))
            
            # Summary stats
            stats = self.db.get_dashboard_stats(self.user_id)
            
            stats_data = [
                ["THỐNG KÊ TỔNG HỢP", ""],
                ["Tổng số nông dân", f"{stats.get('total_farmers', 0)}"],
                ["Tổng số giao dịch", f"{stats.get('total_transactions', 0)}"],
                ["Tổng khối lượng thu mua", f"{stats.get('total_weight', 0):,.1f} kg"],
                ["Tổng doanh thu", f"{stats.get('total_value', 0):,.0f} VNĐ"],
                ["Tổng tồn kho", f"{stats.get('total_stock', 0):,.1f} kg"],
            ]
            
            stats_table = Table(stats_data, colWidths=[200, 150])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 30))
            
            # Build PDF
            doc.build(story)
            
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo PDF ra file:\n{os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi xuất PDF: {e}")
    
    def format_date(self, date_value):
        """Định dạng ngày tháng"""
        if not date_value:
            return ""
        try:
            if isinstance(date_value, str):
                if 'T' in date_value:
                    dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass
        return str(date_value)[:16] if date_value else ""


# Report UI Frame
class ReportFrame(ctk.CTkFrame):
    """Frame quản lý báo cáo"""
    
    def __init__(self, master, db_manager: DatabaseManager, user_id: str, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager
        self.user_id = user_id
        self.report_manager = ReportManager(db_manager, user_id)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Thiết lập giao diện báo cáo"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="📄 HỆ THỐNG BÁO CÁO",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=30)
        
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=50)
        
        # Date range selection
        date_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        date_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(date_frame, text="Khoảng thời gian:", font=ctk.CTkFont(size=14)).pack(pady=10)
        
        date_range_frame = ctk.CTkFrame(date_frame, fg_color="transparent")
        date_range_frame.pack(pady=(0, 10))
        
        ctk.CTkLabel(date_range_frame, text="Từ ngày:").pack(side="left", padx=5)
        self.start_date_entry = ctk.CTkEntry(date_range_frame, width=120, placeholder_text="DD/MM/YYYY")
        self.start_date_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(date_range_frame, text="Đến ngày:").pack(side="left", padx=5)
        self.end_date_entry = ctk.CTkEntry(date_range_frame, width=120, placeholder_text="DD/MM/YYYY")
        self.end_date_entry.pack(side="left", padx=5)
        
        # Report buttons
        reports = [
            ("📊 Báo cáo giao dịch", self.report_manager.export_transactions_to_excel),
            ("💰 Báo cáo công nợ", self.report_manager.export_farmer_debt_to_excel),
            ("📦 Báo cáo tồn kho", self.report_manager.export_inventory_to_excel),
            ("📄 Báo cáo tổng hợp PDF", self.report_manager.export_full_report_to_pdf),
        ]
        
        for title, command in reports:
            btn = ctk.CTkButton(
                main_frame,
                text=title,
                command=command,
                height=60,
                font=ctk.CTkFont(size=14, weight="bold"),
                corner_radius=10
            )
            btn.pack(fill="x", pady=10)