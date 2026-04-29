from models.voucher import Voucher
from datetime import datetime


class VoucherService:
    def __init__(self):
        self.vouchers = {}

    def generate_voucher(self, booking_id, amount):
        voucher_id = f"V-{len(self.vouchers)+1}"
        voucher = Voucher(voucher_id, booking_id, datetime.now(), amount)
        self.vouchers[voucher_id] = voucher
        return voucher
