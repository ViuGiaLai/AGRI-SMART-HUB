# -*- coding: utf-8 -*-
# database/db_manager.py
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from supabase import Client
from .models import *
import logging

try:
    from core.cache_manager import get_cache
    _CACHE_AVAILABLE = True
except ImportError:
    _CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Quản lý database operations"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._cache = get_cache() if _CACHE_AVAILABLE else None
    
    # ============ PRODUCTS MANAGEMENT ============
    
    def create_product(self, product: Product) -> Optional[Dict]:
        """Tạo sản phẩm mới"""
        try:
            data = asdict(product)
            data.pop('id', None)
            result = self.supabase.table('products').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            return None
    
    def get_products(self, user_id: str) -> List[Dict]:
        """Lấy danh sách sản phẩm của user"""
        try:
            result = self.supabase.table('products')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
    
    def update_product(self, product_id: str, data: Dict) -> bool:
        """Cập nhật sản phẩm"""
        try:
            self.supabase.table('products')\
                .update(data)\
                .eq('id', product_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False
    
    def delete_product(self, product_id: str) -> bool:
        """Xóa sản phẩm"""
        try:
            self.supabase.table('products')\
                .delete()\
                .eq('id', product_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False
    
    # ============ GRADING RULES MANAGEMENT ============
    
    def create_grading_rule(self, rule: GradingRule) -> Optional[Dict]:
        """Tạo quy tắc trừ lùi"""
        try:
            data = asdict(rule)
            data.pop('id', None)
            result = self.supabase.table('grading_rules').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating grading rule: {e}")
            return None
    
    def get_grading_rules(self, user_id: str, product_id: Optional[str] = None) -> List[Dict]:
        """Lấy quy tắc trừ lùi"""
        try:
            query = self.supabase.table('grading_rules')\
                .select('*, products(name)')\
                .eq('user_id', user_id)\
                .eq('is_active', True)
            
            if product_id:
                query = query.eq('product_id', product_id)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting grading rules: {e}")
            return []
    
    def update_grading_rule(self, rule_id: str, data: Dict) -> bool:
        """Cập nhật quy tắc trừ lùi"""
        try:
            self.supabase.table('grading_rules')\
                .update(data)\
                .eq('id', rule_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating grading rule: {e}")
            return False
    
    # ============ FARMERS MANAGEMENT ============
    
    def create_farmer(self, farmer: Farmer) -> Optional[Dict]:
        """Thêm nông dân mới"""
        try:
            data = asdict(farmer)
            data.pop('id', None)
            result = self.supabase.table('farmers').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating farmer: {e}")
            return None
    
    def get_farmers(self, user_id: str, search: Optional[str] = None) -> List[Dict]:
        """Lấy danh sách nông dân"""
        try:
            query = self.supabase.table('farmers')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)
            
            if search:
                query = query.or_(f"name.ilike.%{search}%,phone.ilike.%{search}%")
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting farmers: {e}")
            return []
    
    def update_farmer(self, farmer_id: str, data: Dict) -> bool:
        """Cập nhật thông tin nông dân"""
        try:
            self.supabase.table('farmers')\
                .update(data)\
                .eq('id', farmer_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating farmer: {e}")
            return False
    
    def update_farmer_debt(self, farmer_id: str, amount: float, is_increase: bool = True) -> bool:
        """Cập nhật công nợ của nông dân"""
        try:
            # Lấy current debt
            result = self.supabase.table('farmers')\
                .select('total_debt')\
                .eq('id', farmer_id)\
                .execute()
            
            if result.data:
                current_debt = result.data[0]['total_debt']
                new_debt = current_debt + amount if is_increase else current_debt - amount
                new_debt = max(0, new_debt)
                
                self.supabase.table('farmers')\
                    .update({'total_debt': new_debt})\
                    .eq('id', farmer_id)\
                    .execute()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating farmer debt: {e}")
            return False
    
    def delete_farmer(self, farmer_id: str) -> bool:
        """Xóa nông dân"""
        try:
            self.supabase.table('farmers')\
                .delete()\
                .eq('id', farmer_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting farmer: {e}")
            return False
    
    # ============ TRANSACTIONS MANAGEMENT ============
    
    def create_transaction(self, transaction: Transaction, update_inventory: bool = True) -> Optional[Dict]:
        """Tạo giao dịch thu mua mới — invalidate cache dashboard."""
        try:
            data = asdict(transaction)
            data.pop('id', None)
            result = self.supabase.table('transactions').insert(data).execute()

            if result.data and update_inventory:
                self.update_inventory(
                    transaction.user_id,
                    transaction.product_id,
                    transaction.net_weight,
                    is_add=True
                )

                if transaction.payment_status == 'debt':
                    self.update_farmer_debt(
                        transaction.farmer_id,
                        transaction.total_amount,
                        is_increase=False
                    )

            # Invalidate cache dashboard stats
            if self._cache and result.data:
                self._cache.delete_group("stats")

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    def get_transactions(self, user_id: str, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        farmer_id: Optional[str] = None) -> List[Dict]:
        """Lấy danh sách giao dịch"""
        try:
            query = self.supabase.table('transactions')\
                .select('*, farmers(name), products(name)')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)
            
            if start_date:
                query = query.gte('created_at', start_date)
            if end_date:
                query = query.lte('created_at', end_date)
            if farmer_id:
                query = query.eq('farmer_id', farmer_id)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []
    
    def get_transaction_summary(self, user_id: str) -> Dict:
        """Lấy tổng kết giao dịch"""
        try:
            # Tổng số tiền
            result = self.supabase.table('transactions')\
                .select('total_amount, payment_status')\
                .eq('user_id', user_id)\
                .execute()
            
            total_revenue = sum(t['total_amount'] for t in result.data) if result.data else 0
            paid_amount = sum(t['total_amount'] for t in result.data if t['payment_status'] == 'paid') if result.data else 0
            debt_amount = sum(t['total_amount'] for t in result.data if t['payment_status'] == 'debt') if result.data else 0
            
            return {
                'total_transactions': len(result.data) if result.data else 0,
                'total_revenue': total_revenue,
                'paid_amount': paid_amount,
                'debt_amount': debt_amount
            }
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            return {}
    
    # ============ INVENTORY MANAGEMENT ============
    
    def update_inventory(self, user_id: str, product_id: str, quantity: float, is_add: bool = True) -> bool:
        """Cập nhật tồn kho — invalidate cache."""
        try:
            result = self.supabase.table('inventory')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('product_id', product_id)\
                .execute()

            if result.data:
                current_stock = result.data[0]['current_stock']
                new_stock = current_stock + quantity if is_add else current_stock - quantity
                new_stock = max(0, new_stock)

                self.supabase.table('inventory')\
                    .update({
                        'current_stock': new_stock,
                        'last_updated': datetime.now().isoformat()
                    })\
                    .eq('id', result.data[0]['id'])\
                    .execute()
            else:
                self.supabase.table('inventory').insert({
                    'user_id': user_id,
                    'product_id': product_id,
                    'current_stock': quantity if is_add else 0,
                    'last_updated': datetime.now().isoformat()
                }).execute()

            # Invalidate cache tồn kho
            if self._cache:
                self._cache.delete_group("inv")
                self._cache.delete_group("stats")

            return True
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            return False
    
    def get_inventory(self, user_id: str) -> List[Dict]:
        """Lấy danh sách tồn kho — có cache Redis 60s."""
        if self._cache:
            cached = self._cache.get("inv", user_id)
            if cached is not None:
                return cached

        try:
            result = self.supabase.table('inventory')\
                .select('*, products(name)')\
                .eq('user_id', user_id)\
                .execute()
            data = result.data if result.data else []

            if self._cache:
                self._cache.set("inv", data, user_id, ttl=60)
            return data
        except Exception as e:
            logger.error(f"Error getting inventory: {e}")
            return []
    
    # ============ MARKET PRICES ============
    
    def add_market_price(self, price_data: Dict) -> Optional[Dict]:
        """Thêm dữ liệu giá thị trường — invalidate cache."""
        try:
            price_data['log_date'] = date.today().isoformat()
            result = self.supabase.table('market_prices').insert(price_data).execute()

            # Invalidate cache giá thị trường
            if self._cache and result.data:
                product = price_data.get("product_name", "")
                self._cache.delete_group("mp")
                logger.info(f"🗑️ Cache 'mp' invalidated after adding {product}")

            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error adding market price: {e}")
            return None
    
    def get_market_prices(self, product_name: str, days: int = 30) -> List[Dict]:
        """Lấy giá thị trường trong N ngày gần nhất — có cache Redis."""
        # Cache key: mp:{product_slug}:{days}d
        if self._cache:
            cached = self._cache.get("mp", product_name, f"{days}d")
            if cached is not None:
                return cached

        try:
            start_date = (date.today() - timedelta(days=max(days - 1, 0))).isoformat()
            result = self.supabase.table('market_prices')\
                .select('*')\
                .eq('product_name', product_name)\
                .gte('log_date', start_date)\
                .order('log_date', desc=True)\
                .limit(days)\
                .execute()
            data = result.data if result.data else []

            # Lưu cache (TTL: 10 phút cho giá thị trường)
            if self._cache:
                self._cache.set("mp", data, product_name, f"{days}d", ttl=600)

            return data
        except Exception as e:
            logger.error(f"Error getting market prices: {e}")
            return []

    def get_market_prices_any(self, product_names: List[str], days: int = 7) -> List[Dict]:
        """Thử nhiều tên sản phẩm (Cà phê / cà phê) và trả về bộ có dữ liệu.
        Cache handled internally by get_market_prices()."""
        for name in product_names:
            rows = self.get_market_prices(name, days=days)
            if rows:
                return rows
        return []
    
    # ============ STATISTICS & REPORTS ============
    
    def get_dashboard_stats(self, user_id: str) -> Dict:
        """Lấy thống kê cho dashboard — có cache Redis 30s."""
        if self._cache:
            cached = self._cache.get("stats", user_id, "dashboard")
            if cached is not None:
                return cached

        try:
            farmers_result = self.supabase.table('farmers')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            transactions_result = self.supabase.table('transactions')\
                .select('total_amount, net_weight')\
                .eq('user_id', user_id)\
                .execute()
            inventory_result = self.supabase.table('inventory')\
                .select('current_stock')\
                .eq('user_id', user_id)\
                .execute()

            total_weight = sum(t['net_weight'] for t in transactions_result.data) if transactions_result.data else 0
            total_value = sum(t['total_amount'] for t in transactions_result.data) if transactions_result.data else 0
            total_stock = sum(i['current_stock'] for i in inventory_result.data) if inventory_result.data else 0

            data = {
                'total_farmers': farmers_result.count if farmers_result.count else 0,
                'total_transactions': len(transactions_result.data) if transactions_result.data else 0,
                'total_weight': total_weight,
                'total_value': total_value,
                'total_stock': total_stock
            }

            if self._cache:
                self._cache.set("stats", data, user_id, "dashboard", ttl=30)
            return data
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}