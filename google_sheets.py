import gspread
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS_JSON, SHEET_NAME
from models import EmployeeModel, LogistProjectModel, ClientModel, TgUserStatus

logger = logging.getLogger(__name__)

class EmployeeCols:
    ID = 1          
    TG_ID = 2       
    TG_STATUS = 3   
    PHONE = 8       
    LAVOZIM = 10    
    TG_LAVOZIM = 11 
    FULLNAME = 14
    WAKE_STATUS = 15  

class ClientCols:
    CID = 1
    NAME = 3
    PHONE = 6
    TG_ID = 8
    TG_STATUS = 10

class ObjectCols:
    OID = 2         
    START = 3       
    MIJOZ = 5       
    NOMI = 6        
    STATUS = 7      
    VALYUTA = 9     
    BRIGADIR = 11   
    HUDUD = 20      
    YAKUNIY = 21    
    TOLANDI = 22    
    QARZ = 23
    USTA_OID = 30   
    USTA_NOMI = 32  

class ChiqimCols:
    SANA = 1          # "Sana" ustuni
    OMBOR = 2         # "Ombor" ustuni
    MAHSULOT = 4      # "Mahsulot" ustuni
    TURI = 5          # "Turi" ustuni
    SONI = 6          # "Soni" ustuni
    KVM = 7           # "Kv.m" ustuni
    KONTRA = 11       # "Kontragent" ustuni
    OQIM_TURI = 12    # "Oqim Turi" ustuni

class GoogleSheetsRepository:
    def __init__(self):
        logger.info("[REPO] Google API ga ulanmoqda...")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        try:
            # Matn (Railway) yoki Fayl (Lokal) ekanligini tekshiramiz
            if GOOGLE_CREDENTIALS_JSON and GOOGLE_CREDENTIALS_JSON.strip().startswith('{'):
                # Railway uchun: JSON matnidan o'qish
                creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            else:
                # Kompyuter uchun: Fayldan o'qish
                creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_JSON, scopes=scopes)
            
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open(SHEET_NAME)
            
            self.xodimlar_ws = self.sheet.worksheet("Xodimlar")
            self.mijozlar_ws = self.sheet.worksheet("Mijozlar")
            self.obyektlar_ws = self.sheet.worksheet("Obyektlar")
            self.logist_data_ws = self.sheet.worksheet("LogistData")
            self.yangi_mijoz_ws = self.sheet.worksheet("YangiMijoz")
            
            self._cache = {}
            logger.info("[REPO] Sheets bilan ulanish muvaffaqiyatli yakunlandi.")
        except Exception as e:
            logger.critical(f"[REPO XATOLIGI] Google Sheetsga ulanishda xatolik: {e}")
            exit(1)

    def _clean_phone(self, phone: str) -> str:
        return "".join(filter(str.isdigit, str(phone))) if phone else ""

    def _parse_float(self, val: str) -> float:
        try:
            return float(val.replace(',', '.').replace(' ', '')) if val.strip() else 0.0
        except ValueError:
            return 0.0

    def auth_employee(self, phone: str, telegram_id: int, expected_role: str = "logist") -> EmployeeModel:
        phone_clean = self._clean_phone(phone)
        data = self.xodimlar_ws.get_all_values()
        
        for idx, row in enumerate(data[3:], start=4): 
            if len(row) > EmployeeCols.PHONE:
                row_phone = self._clean_phone(row[EmployeeCols.PHONE])
                row_tg_id = row[EmployeeCols.TG_ID].strip() if len(row) > EmployeeCols.TG_ID else ""
                tg_lavozim = row[EmployeeCols.TG_LAVOZIM].strip().lower() if len(row) > EmployeeCols.TG_LAVOZIM else ""
                
                if (row_phone and phone_clean and row_phone[-9:] == phone_clean[-9:]) or \
                   (row_tg_id and row_tg_id == str(telegram_id)):
                    
                    emp_id = row[EmployeeCols.ID].strip()
                    tg_status = row[EmployeeCols.TG_STATUS].strip() if len(row) > EmployeeCols.TG_STATUS else ""
                    
                    if tg_lavozim != expected_role:
                        return EmployeeModel(emp_id, str(telegram_id), "Lavozim Xato", row_phone, "", tg_lavozim, "")

                    needs_update = False
                    if not row_tg_id or row_tg_id != str(telegram_id):
                        self.xodimlar_ws.update_cell(idx, EmployeeCols.TG_ID + 1, str(telegram_id))
                        needs_update = True
                        
                    if not row_phone or (phone_clean and row_phone[-9:] != phone_clean[-9:]):
                        raw_9_digit_phone = phone_clean[-9:] if len(phone_clean) >= 9 else phone_clean
                        self.xodimlar_ws.update_cell(idx, EmployeeCols.PHONE + 1, raw_9_digit_phone)
                        needs_update = True

                    if needs_update and tg_status.lower() != TgUserStatus.REJECTED:
                        self.xodimlar_ws.update_cell(idx, EmployeeCols.TG_STATUS + 1, "Kutmoqda")
                        tg_status = "Kutmoqda"
                    elif tg_status.lower() in [TgUserStatus.NEW, ""]:
                        self.xodimlar_ws.update_cell(idx, EmployeeCols.TG_STATUS + 1, "Kutmoqda")
                        tg_status = "Kutmoqda"

                    return EmployeeModel(
                        emp_id, str(telegram_id), tg_status, phone_clean,
                        row[EmployeeCols.LAVOZIM].strip() if len(row) > EmployeeCols.LAVOZIM else "",
                        row[EmployeeCols.TG_LAVOZIM].strip() if len(row) > EmployeeCols.TG_LAVOZIM else "",
                        row[EmployeeCols.FULLNAME].strip() if len(row) > EmployeeCols.FULLNAME else ""
                    )
        return EmployeeModel("", str(telegram_id), "Topilmadi", "", "", "", "")

    def get_all_admins_tg_ids(self) -> List[int]:
        data = self.xodimlar_ws.get_all_values()
        admin_ids = []
        for row in data[3:]:
            if len(row) > EmployeeCols.TG_LAVOZIM:
                lavozim = row[EmployeeCols.TG_LAVOZIM].strip().lower()
                tg_id = row[EmployeeCols.TG_ID].strip()
                status = row[EmployeeCols.TG_STATUS].strip().lower()
                
                if lavozim == "admin" and tg_id.isdigit() and status == TgUserStatus.APPROVED:
                    admin_ids.append(int(tg_id))
        return admin_ids

    def get_wake_employees(self) -> List[dict]:
        try:
            data = self.xodimlar_ws.get_all_values()
        except Exception as e:
            logger.error(f"Wake xodimlarni o'qishda xato: {e}")
            return []
            
        wake_users = []
        
        for row in data:
            if len(row) > EmployeeCols.WAKE_STATUS:
                tg_id = row[EmployeeCols.TG_ID].strip()
                tg_status = row[EmployeeCols.TG_STATUS].strip().lower()
                wake_status = row[EmployeeCols.WAKE_STATUS].strip().lower()
                
                if tg_id.isdigit() and tg_status == TgUserStatus.APPROVED and wake_status == "wake":
                    wake_users.append({
                        "tg_id": int(tg_id),
                        "full_name": row[EmployeeCols.FULLNAME].strip()
                    })
        return wake_users

    def auth_client(self, phone: str, telegram_id: int) -> ClientModel:
        phone_clean = self._clean_phone(phone)
        data = self.mijozlar_ws.get_all_values()
        
        for idx, row in enumerate(data[1:], start=2): 
            if len(row) > ClientCols.PHONE:
                row_phone = self._clean_phone(row[ClientCols.PHONE])
                row_tg_id = row[ClientCols.TG_ID].strip() if len(row) > ClientCols.TG_ID else ""
                
                if (row_phone and phone_clean and row_phone[-9:] == phone_clean[-9:]) or \
                   (row_tg_id and row_tg_id == str(telegram_id)):
                    
                    cid = row[ClientCols.CID].strip()
                    tg_status = row[ClientCols.TG_STATUS].strip() if len(row) > ClientCols.TG_STATUS else ""
                    name = row[ClientCols.NAME].strip()

                    needs_update = False
                    if not row_tg_id or row_tg_id != str(telegram_id):
                        self.mijozlar_ws.update_cell(idx, ClientCols.TG_ID + 1, str(telegram_id))
                        needs_update = True
                        
                    if not row_phone or (phone_clean and row_phone[-9:] != phone_clean[-9:]):
                        raw_9_digit_phone = phone_clean[-9:] if len(phone_clean) >= 9 else phone_clean
                        self.mijozlar_ws.update_cell(idx, ClientCols.PHONE + 1, raw_9_digit_phone)
                        needs_update = True

                    if needs_update and tg_status.lower() not in [TgUserStatus.REJECTED, TgUserStatus.APPROVED]:
                        self.mijozlar_ws.update_cell(idx, ClientCols.TG_STATUS + 1, "Kutmoqda")
                        tg_status = "Kutmoqda"
                    elif tg_status.lower() in [TgUserStatus.NEW, ""]:
                        self.mijozlar_ws.update_cell(idx, ClientCols.TG_STATUS + 1, "Kutmoqda")
                        tg_status = "Kutmoqda"

                    return ClientModel(cid, name, phone_clean, str(telegram_id), tg_status)
        return ClientModel("", "", "", str(telegram_id), "Topilmadi")

    def save_new_client_attempt(self, tg_id: str, phone: str, full_name: str, username: str, date_time: str):
        try:
            self.yangi_mijoz_ws.append_row([tg_id, phone, full_name, username, date_time])
        except Exception as e:
            logger.error(f"Yangi mijozni saqlashda xatolik: {e}")

    def get_recent_new_clients(self) -> List[dict]:
        try:
            data = self.yangi_mijoz_ws.get_all_values()
        except Exception:
            return []
            
        recent_clients = []
        two_days_ago = datetime.now() - timedelta(days=2)
        
        for row in data[1:]: 
            if len(row) >= 5:
                date_str = row[4].strip()
                try:
                    row_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
                    if row_date >= two_days_ago:
                        recent_clients.append({
                            "tg_id": row[0],
                            "phone": row[1],
                            "full_name": row[2],
                            "username": row[3],
                            "date_time": date_str
                        })
                except ValueError:
                    continue
        
        return recent_clients

    def get_active_objects(self) -> List[LogistProjectModel]:
        now = time.time()
        if "active_objects" in self._cache and now - self._cache["active_objects"]["time"] < 60:
            return self._cache["active_objects"]["data"]

        data = self.obyektlar_ws.get_all_values()
        active_projects = {}
        for row in data[3:]:
            if len(row) > ObjectCols.STATUS:
                oid, status = row[ObjectCols.OID].strip(), row[ObjectCols.STATUS].strip()
                if oid and status.lower() != "yopildi" and oid not in active_projects:
                    mijoz_raw = row[ObjectCols.MIJOZ].strip()
                    client_name = mijoz_raw.split("|")[-1].strip() if "|" in mijoz_raw else mijoz_raw
                    active_projects[oid] = LogistProjectModel(oid, row[ObjectCols.NOMI].strip(), client_name, status)
        
        self._cache["active_objects"] = {"time": now, "data": list(active_projects.values())}
        return list(active_projects.values())

    def get_client_objects(self, cid: str) -> List[LogistProjectModel]:
        now = time.time()
        cache_key = f"client_objects_{cid}"
        if cache_key in self._cache and now - self._cache[cache_key]["time"] < 60:
            return self._cache[cache_key]["data"]

        data = self.obyektlar_ws.get_all_values()
        client_projects = []
        for row in data[3:]:
            if len(row) > ObjectCols.STATUS:
                oid, status = row[ObjectCols.OID].strip(), row[ObjectCols.STATUS].strip()
                mijoz_raw = row[ObjectCols.MIJOZ].strip() if len(row) > ObjectCols.MIJOZ else ""
                row_cid = mijoz_raw.split("|")[0].strip() if "|" in mijoz_raw else ""
                
                if oid and row_cid == cid and status.lower() != "yopildi":
                    client_name = mijoz_raw.split("|")[-1].strip() if "|" in mijoz_raw else mijoz_raw
                    client_projects.append(
                        LogistProjectModel(
                            oid=oid, name=row[ObjectCols.NOMI].strip(), client_name=client_name, status=status, cid=row_cid
                        )
                    )
        
        self._cache[cache_key] = {"time": now, "data": client_projects}
        return client_projects
    
    def get_object_by_oid(self, oid: str) -> Optional[LogistProjectModel]:
        data = self.obyektlar_ws.get_all_values()
        project = None
        ustalar = []
        
        for row in data[3:]:
            if not project and len(row) > ObjectCols.OID and row[ObjectCols.OID].strip() == oid:
                mijoz_raw = row[ObjectCols.MIJOZ].strip() if len(row) > ObjectCols.MIJOZ else ""
                project = LogistProjectModel(
                    oid=oid,
                    name=row[ObjectCols.NOMI].strip() if len(row) > ObjectCols.NOMI else "",
                    client_name=mijoz_raw.split("|")[-1].strip() if "|" in mijoz_raw else mijoz_raw,
                    status=row[ObjectCols.STATUS].strip() if len(row) > ObjectCols.STATUS else "",
                    cid=mijoz_raw.split("|")[0].strip() if "|" in mijoz_raw else "",
                    start_date=row[ObjectCols.START].strip() if len(row) > ObjectCols.START else "",
                    brigadir=row[ObjectCols.BRIGADIR].strip() if len(row) > ObjectCols.BRIGADIR else "",
                    hudud=row[ObjectCols.HUDUD].strip() if len(row) > ObjectCols.HUDUD else "",
                    valyuta=row[ObjectCols.VALYUTA].strip() if len(row) > ObjectCols.VALYUTA else "",
                    yakuniy_summa=row[ObjectCols.YAKUNIY].strip() if len(row) > ObjectCols.YAKUNIY else "0",
                    tolandi=row[ObjectCols.TOLANDI].strip() if len(row) > ObjectCols.TOLANDI else "0",
                    qarzdorlik=row[ObjectCols.QARZ].strip() if len(row) > ObjectCols.QARZ else "0"
                )
            
            if len(row) > ObjectCols.USTA_NOMI and row[ObjectCols.USTA_OID].strip() == oid:
                usta_nomi = row[ObjectCols.USTA_NOMI].strip()
                if usta_nomi and usta_nomi not in ustalar:
                    ustalar.append(usta_nomi)
                    
        if project:
            project.ustalar = ustalar
            return project
            
        return None

    def save_delivery_data(self, emp_id: str, tg_id: str, cid: str, oid: str, txt_id: str, pht_id: str, vid_id: str, date_time: str):
        self.logist_data_ws.append_row([emp_id, tg_id, cid, oid, txt_id, pht_id, vid_id, date_time])

    def get_deliveries_by_oid(self, oid: str) -> List[Dict[str, Any]]:
        try:
            data = self.logist_data_ws.get_all_values()
        except Exception as e:
            return []
            
        return [{
            "emp_id": row[0].strip(), "txt_id": row[4].strip(), "pht_id": row[5].strip(),
            "vid_id": row[6].strip(), "date_time": row[7].strip()
        } for row in data[1:] if len(row) > 7 and row[3].strip() == str(oid)]
    
    def get_object_inventory_summary(self, oid: str) -> dict:
        try:
            chiqim_ws = self.sheet.worksheet("OmborData")
            data = chiqim_ws.get_all_values()
        except Exception as e:
            return {}

        inventory = {}
        for row in data[1:]:
            if len(row) > ChiqimCols.OQIM_TURI:
                if oid in row[ChiqimCols.KONTRA].strip():
                    mahsulot = row[ChiqimCols.MAHSULOT].strip()
                    oqim = row[ChiqimCols.OQIM_TURI].strip().lower()
                    
                    soni, kvm = self._parse_float(row[ChiqimCols.SONI]), self._parse_float(row[ChiqimCols.KVM])
                    if oqim == 'qaytim':
                        soni, kvm = -soni, -kvm
                        
                    if mahsulot not in inventory:
                        inventory[mahsulot] = {'soni': 0.0, 'kvm': 0.0}
                        
                    inventory[mahsulot]['soni'] += soni
                    inventory[mahsulot]['kvm'] += kvm
        return inventory

repo = GoogleSheetsRepository()