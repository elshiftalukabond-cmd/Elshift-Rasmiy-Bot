from dataclasses import dataclass, field

@dataclass
class EmployeeModel:
    emp_id: str
    telegram_id: str
    tg_status: str
    phone: str
    lavozim: str
    tg_lavozim: str
    full_name: str

@dataclass
class ClientModel:
    cid: str
    name: str
    phone: str
    tg_id: str
    tg_status: str

@dataclass
class LogistProjectModel:
    oid: str
    name: str
    client_name: str
    status: str
    cid: str = ""
    start_date: str = ""
    brigadir: str = ""
    hudud: str = ""
    valyuta: str = ""
    yakuniy_summa: str = ""
    tolandi: str = ""
    qarzdorlik: str = ""
    ustalar: list = field(default_factory=list) # YANGI QO'SHILDI

    def format_money(self, amount: str) -> str:
        """Summalarni o'qishga qulay formatga o'tkazadi (Masalan: 1 500 000 so'm)"""
        try:
            if not amount or amount.strip() == "":
                return f"0 {self.valyuta}"
            num = float(amount.replace(",", "").replace(" ", ""))
            v = "$" if self.valyuta.lower() == "dollar" else "so'm"
            return f"{num:,.0f}".replace(",", " ") + f" {v}"
        except ValueError:
            return amount