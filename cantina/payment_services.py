"""Serviços de pagamento (PIX e cartão) — implementações mock/simuladas.

Para produção, troque as chamadas HTTP reais aqui sem mexer na UI.
"""
from __future__ import annotations

import random
import threading
import time
from PySide6.QtCore import QObject, Signal


# ---------------------------------------------------------------- PIX
class PixService(QObject):
    """Gera QR Code Pix (EMV) e observa o pagamento.

    Em produção: chame a API do seu PSP (Mercado Pago, Efí, etc.) para
    gerar o QR e use webhooks para saber do pagamento.
    Aqui: geramos um payload EMV válido e, para simular o banco, disparamos
    `paid` após um tempo aleatório.
    """
    paid = Signal(str)   # emite o txid quando o Pix é confirmado

    def __init__(self, pix_key: str = "cantina@escola.edu.br", merchant: str = "CANTINA ESCOLAR"):
        super().__init__()
        self.pix_key = pix_key
        self.merchant = merchant.upper()[:25]
        self._cancel = False

    @staticmethod
    def _tlv(tag: str, value: str) -> str:
        return f"{tag}{len(value):02d}{value}"

    @staticmethod
    def _crc16(payload: str) -> str:
        crc = 0xFFFF
        for ch in payload.encode("utf-8"):
            crc ^= ch << 8
            for _ in range(8):
                crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
                crc &= 0xFFFF
        return f"{crc:04X}"

    def build_payload(self, amount: float, txid: str) -> str:
        gui = self._tlv("00", "BR.GOV.BCB.PIX")
        key = self._tlv("01", self.pix_key)
        mai = self._tlv("26", gui + key)

        payload = (
            self._tlv("00", "01") +
            mai +
            self._tlv("52", "0000") +
            self._tlv("53", "986") +
            self._tlv("54", f"{amount:.2f}") +
            self._tlv("58", "BR") +
            self._tlv("59", self.merchant) +
            self._tlv("60", "SAO PAULO") +
            self._tlv("62", self._tlv("05", txid[:25]))
        )
        payload += "6304"
        payload += self._crc16(payload)
        return payload

    def watch(self, amount: float, txid: str, timeout: float = 300, fake_delay: tuple[float, float] = (6, 14)):
        self._cancel = False

        def worker():
            wait = random.uniform(*fake_delay)
            elapsed = 0.0
            while elapsed < min(wait, timeout) and not self._cancel:
                time.sleep(0.5)
                elapsed += 0.5
            if not self._cancel:
                self.paid.emit(txid)

        threading.Thread(target=worker, daemon=True).start()

    def cancel(self):
        self._cancel = True


# ---------------------------------------------------------------- Cartão (TEF)
class CardService(QObject):
    """Envia a cobrança para a maquininha (TEF).

    Em produção: use o SDK/CLI da sua adquirente (Stone, Cielo, PagSeguro).
    Aqui apenas simulamos o fluxo.
    """
    approved = Signal(str)
    failed = Signal(str)
    status = Signal(str)

    def __init__(self):
        super().__init__()
        self._cancel = False

    def charge(self, amount: float, kind: str = "credito", fake_delay: tuple[float, float] = (4, 8)):
        self._cancel = False

        def worker():
            self.status.emit("Conectando à maquininha…")
            time.sleep(0.8)
            if self._cancel: return
            self.status.emit("Insira, aproxime ou passe o cartão")
            wait = random.uniform(*fake_delay)
            elapsed = 0.0
            while elapsed < wait and not self._cancel:
                time.sleep(0.5)
                elapsed += 0.5
            if self._cancel: return
            self.status.emit("Processando…")
            time.sleep(1.0)
            if self._cancel: return
            nsu = f"{random.randint(100000, 999999)}"
            self.approved.emit(f"APROVADO • NSU {nsu} • {kind.upper()}")

        threading.Thread(target=worker, daemon=True).start()

    def cancel(self):
        self._cancel = True