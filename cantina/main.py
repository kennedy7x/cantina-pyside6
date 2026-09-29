"""Cantina+ 2.0 — autoatendimento, cozinha, caixa e gestão financeira."""
from __future__ import annotations

import random
import sys
import time
from datetime import date
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap, QTextDocument, QPageSize
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDateEdit, QDoubleSpinBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSpinBox, QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from .database import Database
    from .seed import FLAVORS, icon_for
    from .payment_services import PixService, CardService
except ImportError:
    from database import Database
    from seed import FLAVORS, icon_for
    from payment_services import PixService, CardService


# ========================================================== ESTILO (tema BK)
STYLE = """
* { font-family: 'Segoe UI', Arial; }
QMainWindow, QWidget { background: #fff8f0; color: #2a1a0f; }

#Header { background: #d62300; }
#Header QLabel { color: white; background: transparent; }
#Header QPushButton {
    background: rgba(255,255,255,0.15);
    color: white;
    border: 2px solid rgba(255,255,255,0.4);
}
#Header QPushButton:hover { background: rgba(255,255,255,0.3); }
#Header QPushButton:disabled {
    background: rgba(255,255,255,0.05);
    color: rgba(255,255,255,0.35);
    border: 2px solid rgba(255,255,255,0.15);
}
#Brand { font-size: 26px; font-weight: 900; color: white; letter-spacing: 1px; }
#SubBrand { font-size: 13px; color: #ffe8d6; }
#Hero { background: #f5ebdc; border-radius: 16px; padding: 14px; }

QFrame#ProductCard {
    background: white; border: 2px solid #f5ebdc; border-radius: 16px;
}
QFrame#ProductCard:hover { border: 2px solid #d62300; }
#ProductIcon { background: #fff2e6; border-radius: 34px; font-size: 30px; }
#Price { color: #d62300; font-size: 17px; font-weight: 900; }
#ProductName { font-size: 14px; font-weight: 800; color: #2a1a0f; }
#ProductCat { color: #8a6a4f; font-size: 11px; }

#Card, #SidePanel, #Metric {
    background: white; border: 2px solid #f5ebdc; border-radius: 16px;
}
#MetricValue { color: #d62300; font-size: 26px; font-weight: 900; }
#MetricLabel { color: #8a6a4f; font-size: 12px; font-weight: 700; }

QPushButton {
    border: 0; border-radius: 12px; padding: 11px 18px;
    font-weight: 800; background: #f5ebdc; color: #2a1a0f;
}
QPushButton:hover { background: #ecdfc9; }
QPushButton[primary="true"] { background: #d62300; color: white; }
QPushButton[primary="true"]:hover { background: #b81d00; }
QPushButton[accent="true"] { background: #f5a623; color: #2a1a0f; }
QPushButton[accent="true"]:hover { background: #e0921a; }
QPushButton[warn="true"] { background: #f4a261; color: white; }
QPushButton[danger="true"] { background: #8b0000; color: white; }
QPushButton[ghost="true"] { background: transparent; border: 2px solid #d62300; color: #d62300; }

QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
    background: white; border: 2px solid #f0d9bf; border-radius: 10px; padding: 9px 12px;
    font-size: 14px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 2px solid #d62300; }

QTabWidget::pane { border: 0; }
QTabBar::tab {
    padding: 12px 22px; color: #8a6a4f; font-weight: 800;
    border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 4px;
}
QTabBar::tab:selected { color: white; background: #d62300; }
QTabBar::tab:hover:!selected { color: #d62300; }

QScrollArea { border: 0; background: transparent; }
QTableWidget {
    background: white; border: 2px solid #f5ebdc; border-radius: 12px;
    gridline-color: #f5ebdc; font-size: 13px;
}
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: #ffe3d1; color: #2a1a0f; }
QHeaderView::section {
    background: #d62300; color: white; padding: 10px; border: 0; font-weight: 800;
}
QListWidget { background: white; border: 2px solid #f5ebdc; border-radius: 12px; }
"""


def make_button(text: str, primary=False, danger=False, warn=False, accent=False, ghost=False) -> QPushButton:
    b = QPushButton(text)
    b.setProperty("primary", primary)
    b.setProperty("danger", danger)
    b.setProperty("warn", warn)
    b.setProperty("accent", accent)
    b.setProperty("ghost", ghost)
    return b


def money(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def format_cpf(s: str) -> str:
    d = only_digits(s)[:11]
    if len(d) <= 3: return d
    if len(d) <= 6: return f"{d[:3]}.{d[3:]}"
    if len(d) <= 9: return f"{d[:3]}.{d[3:6]}.{d[6:]}"
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


# ============================================================== TOTEM / KIOSK
class ProductCard(QFrame):
    add_clicked = Signal(object)

    def __init__(self, product: Any):
        super().__init__()
        self.product = product
        self.setObjectName("ProductCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        icon = QLabel(icon_for(product["name"], product["category"]))
        icon.setObjectName("ProductIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedHeight(56)
        lay.addWidget(icon)

        name = QLabel(product["name"])
        name.setObjectName("ProductName")
        name.setWordWrap(True)
        lay.addWidget(name)

        cat = QLabel(product["category"])
        cat.setObjectName("ProductCat")
        lay.addWidget(cat)

        row = QHBoxLayout()
        price = QLabel(money(product["price"]))
        price.setObjectName("Price")
        row.addWidget(price)
        row.addStretch()
        add = make_button("+", primary=True)
        add.setFixedSize(44, 36)
        add.clicked.connect(lambda: self.add_clicked.emit(self.product))
        row.addWidget(add)
        lay.addLayout(row)


class KioskPage(QWidget):
    go_payment = Signal()
    go_account = Signal()
    go_pay_fiado = Signal()

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.student = None
        self.cart: list[dict[str, Any]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(14)

        hero = QFrame(); hero.setObjectName("Hero")
        hl = QHBoxLayout(hero)

        self.user_label = QLabel("Nenhum aluno conectado")
        self.user_label.setStyleSheet("font-size:16px;font-weight:800;color:#2a1a0f;")
        hl.addWidget(self.user_label)

        self.pendura_label = QLabel("")
        self.pendura_label.setStyleSheet("color:#d62300;font-weight:800;")
        hl.addWidget(self.pendura_label)

        hl.addStretch()

        self.b_fiado = make_button("💰 Pagar fiado", warn=True)
        self.b_fiado.clicked.connect(lambda: self.go_pay_fiado.emit())
        self.b_fiado.setEnabled(False)
        hl.addWidget(self.b_fiado)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔎  Buscar produto…")
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self.reload_products)
        hl.addWidget(self.search)

        trocar = make_button("Trocar aluno", accent=True)
        trocar.clicked.connect(lambda: self.go_account.emit())
        hl.addWidget(trocar)
        root.addWidget(hero)

        content = QHBoxLayout()
        root.addLayout(content)

        self.tabs = QTabWidget()
        content.addWidget(self.tabs, 3)

        self.reload_products()
        content.addWidget(self._build_cart(), 1)

    def set_student(self, student: dict):
        self.student = student
        self.user_label.setText(f"👤  {student['name']}  •  {student['class_name']}")
        _, total = self.db.fiado_can_order(student["cpf"])
        self.pendura_label.setText(
            f"Fiado atual: {money(total)} / limite {money(self.db.PENDURA_LIMIT)}"
        )
        if total > 0:
            self.b_fiado.setEnabled(True)
            self.b_fiado.setText(f"💰 Pagar fiado ({money(total)})")
        else:
            self.b_fiado.setEnabled(False)
            self.b_fiado.setText("💰 Sem fiado")

    def reload_products(self) -> None:
        self.tabs.clear()
        query = self.search.text().strip().lower() if hasattr(self, "search") else ""
        all_products = self.db.products()
        if query:
            all_products = [p for p in all_products if query in p["name"].lower()]
        self.tabs.addTab(self._make_scroll(all_products), "Todos")
        for cat in self.db.categories():
            items = [p for p in all_products if p["category"] == cat["name"]]
            if items:
                self.tabs.addTab(self._make_scroll(items), cat["name"])

    def _make_scroll(self, products) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        grid = QGridLayout(host)
        grid.setAlignment(Qt.AlignTop)
        grid.setSpacing(12)
        for i, p in enumerate(products):
            card = ProductCard(p)
            card.add_clicked.connect(self.add_product)
            grid.addWidget(card, i // 4, i % 4)
        scroll.setWidget(host)
        return scroll

    def _build_cart(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("SidePanel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 16, 16, 16)

        t = QLabel("🛒  Seu carrinho")
        t.setStyleSheet("font-size:19px;font-weight:900;color:#d62300;")
        lay.addWidget(t)

        self.cart_list = QListWidget()
        self.cart_list.setMinimumWidth(320)
        lay.addWidget(self.cart_list)

        lay.addWidget(QLabel("Observação do pedido"))
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Ex.: sem açúcar, entregar no intervalo…")
        self.notes.setMaximumHeight(70)
        lay.addWidget(self.notes)

        self.total_label = QLabel("Total  R$ 0,00")
        self.total_label.setStyleSheet("font-size:22px;font-weight:900;color:#d62300;")
        lay.addWidget(self.total_label)

        adv = make_button("Avançar para pagamento  →", primary=True)
        adv.setMinimumHeight(48)
        adv.clicked.connect(self.open_payment)
        lay.addWidget(adv)
        return panel

    def add_product(self, product) -> None:
        name = product["name"]
        flavor_options = FLAVORS.get(name, [])
        if flavor_options:
            from PySide6.QtWidgets import QInputDialog
            flavor, ok = QInputDialog.getItem(
                self, "Escolha o sabor", f"{name} — sabor:", flavor_options, 0, False
            )
            if not ok:
                return
            name = f"{name} ({flavor})"

        for item in self.cart:
            if item["display"] == name:
                item["quantity"] += 1
                break
        else:
            self.cart.append({
                "id": product["id"], "display": name,
                "name": name, "price": product["price"], "quantity": 1,
            })
        self.refresh_cart()

    def change_quantity(self, index: int, delta: int) -> None:
        if 0 <= index < len(self.cart):
            self.cart[index]["quantity"] += delta
            if self.cart[index]["quantity"] <= 0:
                self.cart.pop(index)
            self.refresh_cart()

    def refresh_cart(self) -> None:
        self.cart_list.clear()
        total = 0.0
        for index, item in enumerate(self.cart):
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(4, 4, 4, 4)
            label = QLabel(f"{item['quantity']}x {item['display']}\n"
                           f"{money(item['price'] * item['quantity'])}")
            label.setStyleSheet("font-weight:700;")
            line.addWidget(label)
            line.addStretch()
            minus = make_button("−"); minus.setFixedSize(30, 30)
            plus = make_button("+", accent=True); plus.setFixedSize(30, 30)
            minus.clicked.connect(lambda _=False, i=index: self.change_quantity(i, -1))
            plus.clicked.connect(lambda _=False, i=index: self.change_quantity(i, 1))
            line.addWidget(minus); line.addWidget(plus)
            li = QListWidgetItem()
            li.setSizeHint(row.sizeHint())
            self.cart_list.addItem(li)
            self.cart_list.setItemWidget(li, row)
            total += item["price"] * item["quantity"]
        self.total_label.setText(f"Total  {money(total)}")

    def open_payment(self) -> None:
        if self.student is None:
            QMessageBox.warning(self, "Sem aluno", "Faça login com o CPF antes de pedir.")
            return
        if not self.cart:
            QMessageBox.information(self, "Carrinho vazio", "Adicione pelo menos um produto.")
            return
        pode, total = self.db.fiado_can_order(self.student["cpf"])
        if not pode:
            QMessageBox.critical(
                self, "Fiado bloqueado",
                f"{self.student['name']} já deve R$ {total:.2f}.\n"
                f"Pague o fiado antes de fazer novo pedido "
                f"(limite R$ {self.db.PENDURA_LIMIT:.2f}).",
            )
            return
        self.go_payment.emit()

    def clear_order(self) -> None:
        self.cart.clear()
        self.notes.clear()
        self.refresh_cart()


# ============================================================== CONTA (CPF)
class AccountPage(QWidget):
    logged = Signal(dict)

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)

        card = QFrame(); card.setObjectName("Card")
        card.setFixedWidth(480)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(36, 36, 36, 36)
        cl.setSpacing(12)

        title = QLabel("🍔  Cantina+")
        title.setStyleSheet("font-size:34px;font-weight:900;color:#d62300;")
        title.setAlignment(Qt.AlignCenter)
        cl.addWidget(title)

        sub = QLabel("Faça login com o CPF ou crie sua conta")
        sub.setStyleSheet("color:#8a6a4f;font-size:13px;")
        sub.setAlignment(Qt.AlignCenter)
        cl.addWidget(sub)

        cl.addSpacing(10)

        self.cpf = QLineEdit()
        self.cpf.setPlaceholderText("CPF (somente números)")
        self.cpf.setMaxLength(14)
        self.cpf.textChanged.connect(self._mask_cpf)
        self.cpf.returnPressed.connect(self._lookup)
        cl.addWidget(self.cpf)

        self.name = QLineEdit(); self.name.setPlaceholderText("Nome completo")
        self.class_name = QLineEdit(); self.class_name.setPlaceholderText("Turma (ex.: 8º A)")
        cl.addWidget(self.name)
        cl.addWidget(self.class_name)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color:#8a6a4f;")
        cl.addWidget(self.status)

        self.enter_btn = make_button("Continuar", primary=True)
        self.enter_btn.setMinimumHeight(48)
        self.enter_btn.clicked.connect(self._lookup)
        cl.addWidget(self.enter_btn)

        root.addWidget(card, alignment=Qt.AlignCenter)
        self._show_register(False)

    def _mask_cpf(self):
        self.cpf.blockSignals(True)
        self.cpf.setText(format_cpf(self.cpf.text()))
        self.cpf.blockSignals(False)

    def _show_register(self, show: bool):
        self.name.setVisible(show)
        self.class_name.setVisible(show)
        self.enter_btn.setText("Criar conta e entrar" if show else "Entrar com CPF")

    def _lookup(self):
        cpf = only_digits(self.cpf.text())
        if len(cpf) != 11:
            QMessageBox.warning(self, "CPF inválido", "Digite os 11 dígitos do CPF.")
            return

        student = self.db.get_student(cpf)
        if student:
            self.logged.emit(dict(student))
            return

        if not self.name.isVisible():
            self._show_register(True)
            self.status.setText("CPF não encontrado. Preencha nome e turma para criar a conta.")
            return

        name = self.name.text().strip()
        cls = self.class_name.text().strip()
        if not name or not cls:
            QMessageBox.warning(self, "Dados", "Informe nome e turma para criar a conta.")
            return

        self.db.create_student(cpf, name, cls)
        student = self.db.get_student(cpf)
        QMessageBox.information(self, "Bem-vindo!", f"Conta criada para {name}.")
        self.logged.emit(dict(student))

    def reset(self):
        self.cpf.clear(); self.name.clear(); self.class_name.clear()
        self.status.clear()
        self._show_register(False)


# ============================================================== PAGAMENTO
class PaymentPage(QWidget):
    paid = Signal(str)
    back = Signal()

    def __init__(self, db: Database, kiosk: KioskPage):
        super().__init__()
        self.db = db
        self.kiosk = kiosk
        self.remaining = 300
        self.chosen_method = None
        self.card_kind = None
        self.mode = "order"

        self.pix = PixService()
        self.card = CardService()
        self.pix.paid.connect(self._on_pix_paid)
        self.card.approved.connect(self._on_card_approved)
        self.card.failed.connect(self._on_card_failed)
        self.card.status.connect(self._on_card_status)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._header_labels: list[tuple[QLabel, QLabel]] = []

        self.stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.addWidget(self.stack, 1)

        back = make_button("← Voltar ao carrinho", ghost=True)
        back.clicked.connect(self._go_back)
        outer.addWidget(back, alignment=Qt.AlignLeft)

        self.stack.addWidget(self._page_menu())     # 0
        self.stack.addWidget(self._page_pix())      # 1
        self.stack.addWidget(self._page_card())     # 2
        self.stack.addWidget(self._page_cash())     # 3
        self.stack.addWidget(self._page_fiado())    # 4

    # ----------------------------------------------------- header reutilizável
    def _make_header(self) -> QWidget:
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignCenter)

        big = QLabel("💳  Pagamento")
        big.setAlignment(Qt.AlignCenter)
        big.setStyleSheet("font-size:34px;font-weight:900;color:#d62300;letter-spacing:1px;")
        lay.addWidget(big)

        student_lbl = QLabel("👤  —")
        student_lbl.setAlignment(Qt.AlignCenter)
        student_lbl.setStyleSheet(
            "font-size:17px;font-weight:800;color:#2a1a0f;"
            "background:#f5ebdc;border-radius:12px;padding:8px 20px;"
        )
        lay.addWidget(student_lbl, alignment=Qt.AlignCenter)

        total_lbl = QLabel("Total a pagar: —")
        total_lbl.setAlignment(Qt.AlignCenter)
        total_lbl.setStyleSheet("font-size:15px;font-weight:800;color:#8a6a4f;")
        lay.addWidget(total_lbl)

        self._header_labels.append((student_lbl, total_lbl))
        return box

    def _update_header(self):
        student = self.kiosk.student
        nome = student["name"] if student else "—"
        total = self._total()
        label_total = "Fiado em aberto" if self.mode == "fiado" else "Total a pagar"
        for student_lbl, total_lbl in self._header_labels:
            student_lbl.setText(f"👤  {nome}")
            total_lbl.setText(f"{label_total}: {money(total)}")

    # ---------------- MENU ----------------
    def _page_menu(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        lay.addWidget(self._make_header())

        subtitle = QLabel("Escolha a forma de pagamento")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size:16px;font-weight:700;color:#8a6a4f;")
        lay.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignCenter)
        for i, (label, icon, slot) in enumerate([
            ("PIX",      "🟢", self._open_pix),
            ("Cartão",   "💳", self._open_card),
            ("Dinheiro", "💵", self._open_cash),
            ("Fiado",    "📒", self._open_fiado),
        ]):
            b = QPushButton(f"{icon}\n{label}")
            b.setMinimumSize(220, 150)
            b.setStyleSheet("""
                QPushButton {
                    background:white; border:3px solid #f5ebdc; border-radius:20px;
                    font-size:24px; font-weight:900; color:#2a1a0f;
                }
                QPushButton:hover { border:3px solid #d62300; color:#d62300; }
            """)
            b.clicked.connect(slot)
            grid.addWidget(b, i // 2, i % 2)
        lay.addLayout(grid)
        lay.addStretch()
        return w

    # ---------------- PIX ----------------
    def _page_pix(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        lay.addWidget(self._make_header())

        hint = QLabel("Escaneie o QR Code abaixo com o app do banco")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size:18px;font-weight:800;color:#2a1a0f;")
        lay.addWidget(hint)

        self.qr_label = QLabel()
        self.qr_label.setFixedSize(320, 320)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setStyleSheet("background:white;border:12px solid white;border-radius:16px;")
        lay.addWidget(self.qr_label, alignment=Qt.AlignCenter)

        self.pix_status = QLabel("Aguardando confirmação do banco…")
        self.pix_status.setAlignment(Qt.AlignCenter)
        self.pix_status.setStyleSheet("font-size:16px;color:#8a6a4f;font-weight:700;")
        lay.addWidget(self.pix_status)

        self.pix_timer = QLabel("Expira em 05:00")
        self.pix_timer.setAlignment(Qt.AlignCenter)
        self.pix_timer.setStyleSheet("color:#d62300;font-weight:800;")
        lay.addWidget(self.pix_timer)

        cancelar = make_button("Cancelar", ghost=True)
        cancelar.clicked.connect(self._go_back)
        lay.addWidget(cancelar, alignment=Qt.AlignCenter)

        lay.addStretch()
        return w

    def _open_pix(self):
        self.chosen_method = "PIX"
        self._update_header()
        total = self._total()
        txid = f"CANTINA{random.randint(1000, 9999)}"
        self._pix_txid = txid
        payload = self.pix.build_payload(total, txid)
        self._render_qr(payload)

        self.remaining = 300
        self._timer.start(1000)
        self.pix_status.setText("Aguardando confirmação do banco…")
        self.pix.watch(total, txid)
        self.stack.setCurrentIndex(1)

    def _render_qr(self, text: str):
        if qrcode is None:
            self.qr_label.setText("QR PIX\n(sem biblioteca qrcode)")
            return
        qr = qrcode.make(text).convert("RGB").resize((300, 300))
        img = QImage(qr.tobytes(), qr.width, qr.height, QImage.Format_RGB888)
        self.qr_label.setPixmap(QPixmap.fromImage(img))

    def _on_pix_paid(self, txid: str):
        if self.chosen_method != "PIX":
            return
        self._timer.stop()
        self.pix_status.setText("✅ Pagamento confirmado!")
        QTimer.singleShot(900, lambda: self._finish("PIX", "Pago"))

    # ---------------- CARTÃO ----------------
    def _page_card(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        lay.addWidget(self._make_header())

        title = QLabel("Passe o cartão na maquininha")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:22px;font-weight:900;color:#d62300;")
        lay.addWidget(title)

        sub = QLabel("Escolha o tipo de operação abaixo")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#8a6a4f;font-size:14px;")
        lay.addWidget(sub)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        credito = QPushButton("💳  Crédito")
        debito = QPushButton("💳  Débito")
        for b in (credito, debito):
            b.setMinimumSize(220, 140)
            b.setStyleSheet("""
                QPushButton {
                    background:white; border:3px solid #f5ebdc; border-radius:20px;
                    font-size:22px; font-weight:900; color:#2a1a0f;
                }
                QPushButton:hover { border:3px solid #d62300; color:#d62300; }
            """)
        credito.clicked.connect(lambda: self._start_card("credito"))
        debito.clicked.connect(lambda: self._start_card("debito"))
        row.addWidget(credito); row.addWidget(debito)
        lay.addLayout(row)

        self.card_status = QLabel("")
        self.card_status.setAlignment(Qt.AlignCenter)
        self.card_status.setStyleSheet("font-size:16px;color:#8a6a4f;font-weight:700;")
        lay.addWidget(self.card_status)

        cancelar = make_button("Cancelar", ghost=True)
        cancelar.clicked.connect(self._go_back)
        lay.addWidget(cancelar, alignment=Qt.AlignCenter)

        lay.addStretch()
        return w

    def _open_card(self):
        self.chosen_method = "Cartão"
        self.card_kind = None
        self.card_status.setText("")
        self._update_header()
        self.stack.setCurrentIndex(2)

    def _start_card(self, kind: str):
        self.card_kind = kind
        self.card_status.setText("Iniciando cobrança na maquininha…")
        self.card.charge(self._total(), kind=kind)

    def _on_card_status(self, msg: str):
        self.card_status.setText(msg)

    def _on_card_approved(self, nsu: str):
        self.card_status.setText(f"✅ {nsu}")
        QTimer.singleShot(900, lambda: self._finish("Cartão", "Pago"))

    def _on_card_failed(self, msg: str):
        self.card_status.setText(f"❌ {msg}")
        QMessageBox.warning(self, "Cartão recusado", msg)

    # ---------------- DINHEIRO ----------------
    def _page_cash(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        lay.addWidget(self._make_header())

        title = QLabel("💵  Pagamento em dinheiro")
        title.setStyleSheet("font-size:22px;font-weight:900;color:#d62300;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        hint = QLabel("Dirija-se ao caixa e efetue o pagamento.\nO operador confirmará o recebimento.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:#8a6a4f;")
        lay.addWidget(hint)

        confirm = make_button("Operador confirmou o recebimento", primary=True)
        confirm.setMinimumHeight(50)
        confirm.clicked.connect(lambda: self._finish("Dinheiro", "Pago"))
        lay.addWidget(confirm, alignment=Qt.AlignCenter)

        cancelar = make_button("Cancelar", ghost=True)
        cancelar.clicked.connect(self._go_back)
        lay.addWidget(cancelar, alignment=Qt.AlignCenter)

        lay.addStretch()
        return w

    def _open_cash(self):
        self.chosen_method = "Dinheiro"
        self._update_header()
        self.stack.setCurrentIndex(3)

    # ---------------- FIADO ----------------
    def _page_fiado(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        lay.addWidget(self._make_header())

        icon = QLabel("📒")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size:64px;")
        lay.addWidget(icon)

        title = QLabel("Fiado")
        title.setStyleSheet("font-size:28px;font-weight:900;color:#d62300;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("O valor será somado à conta do aluno e cobrado depois.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#8a6a4f;font-size:14px;")
        lay.addWidget(sub)

        lay.addSpacing(8)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(460)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 22, 24, 22)
        cl.setSpacing(10)

        self.fiado_info = QLabel()
        self.fiado_info.setWordWrap(True)
        self.fiado_info.setStyleSheet("font-size:15px;color:#2a1a0f;")
        cl.addWidget(self.fiado_info)

        lay.addWidget(card, alignment=Qt.AlignCenter)

        bar_wrap = QFrame()
        bar_wrap.setFixedWidth(460); bar_wrap.setFixedHeight(14)
        wl = QVBoxLayout(bar_wrap); wl.setContentsMargins(0, 0, 0, 0)
        self.fiado_bar = QFrame()
        self.fiado_bar.setFixedHeight(14)
        self.fiado_bar.setStyleSheet("background:#f0d9bf;border-radius:7px;")
        self.fiado_fill = QFrame(self.fiado_bar)
        self.fiado_fill.setStyleSheet("background:#d62300;border-radius:7px;")
        self.fiado_fill.setFixedHeight(14)
        wl.addWidget(self.fiado_bar)
        lay.addWidget(bar_wrap, alignment=Qt.AlignCenter)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        cancelar = make_button("Cancelar", ghost=True)
        cancelar.setMinimumSize(180, 50)
        cancelar.clicked.connect(self._go_back)

        confirm = make_button("Confirmar fiado", accent=True)
        confirm.setMinimumSize(220, 50)
        confirm.clicked.connect(self._confirm_fiado)

        row.addWidget(cancelar); row.addWidget(confirm)
        lay.addLayout(row)

        lay.addStretch()
        return w

    def _open_fiado(self):
        if self.mode == "fiado":
            QMessageBox.information(self, "Fiado", "Você está pagando o fiado, não pode abrir outro.")
            return
        self.chosen_method = "Fiado"
        student = self.kiosk.student
        if student is None:
            QMessageBox.warning(self, "Sem aluno", "Faça login antes.")
            self._go_back(); return

        _, atual = self.db.fiado_can_order(student["cpf"])
        novo = self._total()
        total = atual + novo
        limite = self.db.PENDURA_LIMIT
        pct = min(100, int(total / limite * 100)) if limite > 0 else 0

        self.fiado_info.setText(
            f"👤  <b>{student['name']}</b>  •  {student['class_name']}<br><br>"
            f"Fiado atual: <b>{money(atual)}</b><br>"
            f"Este pedido: <b>{money(novo)}</b><br>"
            f"<span style='color:#d62300;'>Novo total: <b>{money(total)}</b></span><br>"
            f"Limite: {money(limite)}  ({pct}%)"
        )
        self.fiado_fill.setFixedWidth(int(460 * pct / 100))
        self._update_header()
        self.stack.setCurrentIndex(4)

    def _confirm_fiado(self):
        student = self.kiosk.student
        total_novo = self._total()
        _, atual = self.db.fiado_can_order(student["cpf"])
        if atual + total_novo > self.db.PENDURA_LIMIT:
            QMessageBox.warning(
                self, "Limite de fiado",
                f"Este pedido ultrapassaria o limite de {money(self.db.PENDURA_LIMIT)}."
            )
            return
        self._finish("Fiado", "Pendente")

    # ---------------- ciclo ----------------
    def prepare(self) -> None:
        self.mode = "order"
        self.chosen_method = None
        self.card_kind = None
        self.remaining = 300
        self.pix_status.setText("Aguardando confirmação do banco…")
        self.card_status.setText("")
        self._update_header()
        self.stack.setCurrentIndex(0)

    def prepare_fiado(self) -> None:
        self.mode = "fiado"
        student = self.kiosk.student
        if student is None:
            QMessageBox.warning(self, "Sem aluno", "Faça login antes.")
            return
        _, total = self.db.fiado_can_order(student["cpf"])
        if total <= 0:
            QMessageBox.information(self, "Sem fiado", "Você não tem fiado em aberto.")
            return
        self.chosen_method = None
        self.card_kind = None
        self.remaining = 300
        self.pix_status.setText("Aguardando confirmação do banco…")
        self.card_status.setText("")
        self._update_header()
        self.stack.setCurrentIndex(0)

    def _total(self) -> float:
        if self.mode == "fiado" and self.kiosk.student:
            _, total = self.db.fiado_can_order(self.kiosk.student["cpf"])
            return total
        return sum(i["price"] * i["quantity"] for i in self.kiosk.cart)

    def _tick(self):
        self.remaining = max(0, self.remaining - 1)
        self.pix_timer.setText(f"Expira em {self.remaining // 60:02d}:{self.remaining % 60:02d}")
        if self.remaining == 0:
            self._timer.stop()
            self.pix.cancel()
            self.pix_status.setText("⏱  QR Code expirado.")
            QTimer.singleShot(1200, self._go_back)

    def _go_back(self):
        self._timer.stop()
        self.pix.cancel()
        self.card.cancel()
        self.stack.setCurrentIndex(0)
        self.back.emit()

    def _finish(self, method: str, payment_status: str):
        self._timer.stop()
        self.pix.cancel()
        self.card.cancel()
        student = self.kiosk.student
        if student is None:
            return

        if self.mode == "fiado":
            self.db.pay_fiado(student["cpf"])
            self.kiosk.set_student(student)
            QMessageBox.information(self, "Fiado quitado", "Pagamento registrado. Fiado zerado!")
            self.back.emit()
            return

        number = self.db.create_order(
            student["cpf"], student["name"], student["class_name"],
            self.kiosk.notes.toPlainText().strip(),
            method, payment_status, self.kiosk.cart,
        )
        self.paid.emit(number)


# ============================================================== SUCESSO
class SuccessPage(QWidget):
    back_home = Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        card = QFrame(); card.setObjectName("Card")
        card.setFixedWidth(560)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(14)

        check = QLabel("✓")
        check.setAlignment(Qt.AlignCenter)
        check.setStyleSheet("font-size:70px;color:#d62300;font-weight:900;")
        cl.addWidget(check)

        title = QLabel("PEDIDO CONFIRMADO")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:22px;font-weight:900;color:#d62300;letter-spacing:2px;")
        cl.addWidget(title)

        sub = QLabel("Aguarde ser chamado pelo número")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#8a6a4f;font-size:14px;")
        cl.addWidget(sub)

        self.senha_label = QLabel("—")
        self.senha_label.setAlignment(Qt.AlignCenter)
        self.senha_label.setStyleSheet("""
            font-size:64px; font-weight:900; color:#d62300;
            background:#fff2e6; border-radius:16px; padding:18px;
        """)
        cl.addWidget(self.senha_label)

        self.total_label = QLabel()
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setStyleSheet("font-size:15px;color:#2a1a0f;")
        cl.addWidget(self.total_label)

        b = make_button("Fazer novo pedido", primary=True)
        b.setMinimumHeight(46)
        b.clicked.connect(self.back_home.emit)
        cl.addWidget(b)

        lay.addWidget(card, alignment=Qt.AlignCenter)

    def set_number(self, number: str, total: float = 0.0) -> None:
        self.senha_label.setText(number.split("-")[-1])
        self.total_label.setText(f"Total: {money(total)}")


# ============================================================== COZINHA
class OrderCard(QFrame):
    def __init__(self, order, on_status):
        super().__init__()
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        h = QLabel(f"Senha {order['order_number'].split('-')[-1]}")
        h.setStyleSheet("font-size:20px;font-weight:900;color:#d62300;")
        lay.addWidget(h)

        lay.addWidget(QLabel(f"👤 {order['student_name']} • {order['class_name']}"))

        items = QLabel(order["items"] or "Sem itens")
        items.setWordWrap(True)
        items.setStyleSheet("font-weight:700;")
        lay.addWidget(items)

        pg = order["payment_method"]; pst = order["payment_status"]
        color = "#18a999" if pst == "Pago" else "#d62300"
        info = QLabel(f"💳 {pg} ({pst})\n📝 {order['notes'] or '—'}")
        info.setStyleSheet(f"color:{color};font-size:12px;")
        lay.addWidget(info)

        acts = QHBoxLayout()
        if order["status"] == "Recebido":
            b = make_button("▶ Iniciar preparo", accent=True)
            b.clicked.connect(lambda: on_status(order["id"], "Em Preparo"))
            acts.addWidget(b)
        elif order["status"] == "Em Preparo":
            b = make_button("✔ Marcar pronto", primary=True)
            b.clicked.connect(lambda: on_status(order["id"], "Pronto"))
            acts.addWidget(b)
        elif order["status"] == "Pronto":
            b = make_button("📦 Entregar", primary=True)
            b.clicked.connect(lambda: on_status(order["id"], "Entregue"))
            acts.addWidget(b)

        if pst == "Pendente":
            pay = make_button("💰 Marcar pago", accent=True)
            pay.clicked.connect(lambda: on_status(order["id"], None, True))
            acts.addWidget(pay)

        if acts.count():
            lay.addLayout(acts)


class KitchenPage(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.root = QVBoxLayout(self)
        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10000)

    def refresh(self) -> None:
        while self.root.count():
            it = self.root.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
            elif it.layout():
                self._clear_layout(it.layout())

        top = QHBoxLayout()
        t = QLabel("👨‍🍳  Painel da cozinha")
        t.setStyleSheet("font-size:28px;font-weight:900;color:#d62300;")
        top.addWidget(t); top.addStretch()
        rf = make_button("↻ Atualizar fila", accent=True)
        rf.clicked.connect(self.refresh)
        top.addWidget(rf)
        self.root.addLayout(top)

        cols = QHBoxLayout()
        self.root.addLayout(cols)
        for status, title, color in [
            ("Recebido", "🆕 Recebidos", "#f5a623"),
            ("Em Preparo", "🔥 Em preparo", "#d62300"),
            ("Pronto", "✅ Prontos", "#18a999"),
        ]:
            cols.addWidget(self._column(status, title, color))

    def _column(self, status, title, color):
        box = QFrame()
        box.setObjectName("Card")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 12, 12, 12)

        header = QLabel(title)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            f"font-size:18px;font-weight:900;color:white;background:{color};"
            "border-radius:10px;padding:10px;"
        )
        lay.addWidget(header)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        host = QWidget(); vbox = QVBoxLayout(host)
        vbox.setAlignment(Qt.AlignTop); vbox.setSpacing(10)
        orders = self.db.orders(active_only=True, status=status)
        if not orders:
            empty = QLabel("— vazio —")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color:#8a6a4f;padding:20px;")
            vbox.addWidget(empty)
        for o in orders:
            vbox.addWidget(OrderCard(o, self._on_action))
        scroll.setWidget(host)
        lay.addWidget(scroll)
        return box

    def _clear_layout(self, layout):
        while layout.count():
            it = layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
            elif it.layout():
                self._clear_layout(it.layout())

    def _on_action(self, order_id, new_status, mark_paid=False):
        if mark_paid:
            self.db.set_payment_status(order_id, "Pago")
        if new_status:
            self.db.set_order_status(order_id, new_status)
        self.refresh()


# ============================================================== ADMIN
class AdminPage(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.selected_product_id = None
        lay = QVBoxLayout(self)
        t = QLabel("📊  Administração")
        t.setStyleSheet("font-size:28px;font-weight:900;color:#d62300;")
        lay.addWidget(t)
        tabs = QTabWidget()
        tabs.addTab(self._products_tab(), "Cardápio e estoque")
        tabs.addTab(self._penduras_tab(), "Fiados")
        tabs.addTab(self._expenses_tab(), "Despesas")
        tabs.addTab(self._reports_tab(), "Relatórios financeiros")
        tabs.addTab(self._security_tab(), "Segurança")
        lay.addWidget(tabs)

    # ---------- produtos ----------
    def _products_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Produto", "Categoria", "Preço", "Custo", "Ativo", "Estoque"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.load_selected)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.table)

        form = QHBoxLayout()
        self.name = QLineEdit(); self.name.setPlaceholderText("Nome")
        self.category = QComboBox()
        self.category.addItems([r["name"] for r in self.db.categories()])
        self.price = QLineEdit(); self.price.setPlaceholderText("Preço")
        self.cost = QLineEdit(); self.cost.setPlaceholderText("Custo")
        self.stock = QComboBox(); self.stock.addItems(["Em estoque", "Esgotado"])

        save = make_button("Cadastrar / salvar", primary=True)
        save.clicked.connect(self.save_product)

        self.toggle_active_btn = make_button("Ativar / Desativar", danger=True)
        self.toggle_active_btn.clicked.connect(self.toggle_active)

        toggle = make_button("Alternar estoque", accent=True)
        toggle.clicked.connect(self.toggle_stock)

        for widget in (self.name, self.category, self.price, self.cost,
                       self.stock, save, self.toggle_active_btn, toggle):
            form.addWidget(widget)
        lay.addLayout(form)
        self.load_products()
        return w

    def load_products(self):
        self.table.setRowCount(0)
        for p in self.db.products(active_only=False):
            r = self.table.rowCount(); self.table.insertRow(r)
            id_item = QTableWidgetItem(str(p["id"]))
            id_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            id_item.setData(Qt.UserRole, p["id"])
            self.table.setItem(r, 0, id_item)
            for c, v in enumerate([
                p["name"], p["category"], money(p["price"]), money(p["cost"]),
                "Sim" if p["active"] else "Não",
                "Sim" if p["stock"] else "Não",
            ], start=1):
                item = QTableWidgetItem(str(v))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(r, c, item)

    def load_selected(self, row, column):
        id_item = self.table.item(row, 0)
        if id_item is None:
            return
        self.selected_product_id = id_item.data(Qt.UserRole)
        self.name.setText(self.table.item(row, 1).text())
        self.category.setCurrentText(self.table.item(row, 2).text())
        self.price.setText(
            self.table.item(row, 3).text().replace("R$ ", "").replace(".", "").replace(",", ".")
        )
        self.cost.setText(
            self.table.item(row, 4).text().replace("R$ ", "").replace(".", "").replace(",", ".")
        )
        self.stock.setCurrentIndex(0 if self.table.item(row, 6).text() == "Sim" else 1)
        ativo = self.table.item(row, 5).text() == "Sim"
        self.toggle_active_btn.setText("Desativar" if ativo else "Ativar")

    def save_product(self):
        try:
            price = float(self.price.text().replace(",", ".")); assert price >= 0
            cost = float(self.cost.text().replace(",", ".")) if self.cost.text() else 0
        except Exception:
            QMessageBox.warning(self, "Valor inválido", "Preço/custo inválidos.")
            return
        if not self.name.text().strip():
            QMessageBox.warning(self, "Nome", "Informe o nome.")
            return

        acao = "Atualizar" if self.selected_product_id else "Cadastrar"
        resp = QMessageBox.question(
            self, f"Confirmar {acao.lower()}",
            f"{acao} o produto “{self.name.text().strip()}” "
            f"em {self.category.currentText()} por {money(price)}?"
        )
        if resp != QMessageBox.Yes:
            return

        self.db.save_product(self.selected_product_id, self.name.text().strip(),
                             self.category.currentText(), price, cost,
                             1, 1 if self.stock.currentIndex() == 0 else 0)
        self.selected_product_id = None
        self.name.clear(); self.price.clear(); self.cost.clear()
        self.load_products()

    def toggle_active(self):
        if self.selected_product_id is None:
            return QMessageBox.information(self, "Seleção", "Clique em um produto.")
        nome = self.name.text() or f"ID {self.selected_product_id}"
        ativo = self.toggle_active_btn.text().strip().lower() == "desativar"
        acao = "Desativar" if ativo else "Reativar"
        if QMessageBox.question(
            self, f"Confirmar {acao.lower()}",
            f"{acao} “{nome}”?"
        ) != QMessageBox.Yes:
            return
        self.db.toggle_product_active(self.selected_product_id)
        self.selected_product_id = None
        self.load_products()

    def toggle_stock(self):
        if self.selected_product_id is None:
            return QMessageBox.information(self, "Seleção", "Clique em um produto.")
        nome = self.name.text() or f"ID {self.selected_product_id}"
        em_estoque = self.stock.currentIndex() == 0
        acao = "Marcar como ESGOTADO" if em_estoque else "Marcar como EM ESTOQUE"
        if QMessageBox.question(
            self, "Confirmar estoque",
            f"{acao} o produto “{nome}”?"
        ) != QMessageBox.Yes:
            return
        current = 1 if em_estoque else 0
        self.db.set_stock(self.selected_product_id, 1 - current)
        self.load_products()

    # ---------- fiados ----------
    def _penduras_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        top = QHBoxLayout()
        top.addWidget(QLabel(f"Limite de fiado por aluno: {money(self.db.PENDURA_LIMIT)}"))
        top.addStretch()
        upd = make_button("Atualizar", primary=True)
        upd.clicked.connect(self.load_penduras)
        top.addWidget(upd)
        lay.addLayout(top)

        self.pend_table = QTableWidget(0, 4)
        self.pend_table.setHorizontalHeaderLabels(["Aluno", "Turma", "Deve", "Ação"])
        self.pend_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pend_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pend_table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.pend_table)
        self.load_penduras()
        return w

    def load_penduras(self):
        self.pend_table.setRowCount(0)
        rows = self.db.fiados_por_aluno()
        if not rows:
            self.pend_table.insertRow(0)
            self.pend_table.setItem(0, 0, QTableWidgetItem("— nenhum fiado em aberto —"))
            return
        for r in rows:
            row = self.pend_table.rowCount(); self.pend_table.insertRow(row)
            self.pend_table.setItem(row, 0, QTableWidgetItem(r["student_name"]))
            self.pend_table.setItem(row, 1, QTableWidgetItem(r["class_name"]))
            self.pend_table.setItem(row, 2, QTableWidgetItem(money(r["total"])))
            btn = make_button("Marcar como pago", primary=True)
            btn.clicked.connect(
                lambda _=False, cpf=r["student_cpf"], nome=r["student_name"]: self.pay_pendura(cpf, nome)
            )
            self.pend_table.setCellWidget(row, 3, btn)

    def pay_pendura(self, cpf: str, nome: str):
        if QMessageBox.question(
            self, "Confirmar pagamento",
            f"Marcar todos os fiados de {nome} como pagos?"
        ) != QMessageBox.Yes:
            return
        self.db.pay_fiado(cpf)
        self.load_penduras()
        QMessageBox.information(self, "OK", "Fiado quitado.")

    # ---------- despesas ----------
    def _expenses_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        form = QHBoxLayout()
        self.exp_desc = QLineEdit(); self.exp_desc.setPlaceholderText("Descrição")
        self.exp_cat = QComboBox()
        self.exp_cat.addItems(["Ingredientes", "Embalagens", "Equipamento",
                               "Manutenção", "Pessoal", "Outros"])
        self.exp_val = QDoubleSpinBox(); self.exp_val.setMaximum(100000)
        self.exp_val.setPrefix("R$ ")
        add = make_button("Registrar despesa", primary=True)
        add.clicked.connect(self.add_expense)
        for widget in (self.exp_desc, self.exp_cat, self.exp_val, add):
            form.addWidget(widget)
        lay.addLayout(form)

        self.exp_table = QTableWidget(0, 4)
        self.exp_table.setHorizontalHeaderLabels(["Data", "Descrição", "Categoria", "Valor"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.exp_table)
        self.load_expenses()
        return w

    def load_expenses(self):
        self.exp_table.setRowCount(0)
        for e in self.db.expenses():
            r = self.exp_table.rowCount(); self.exp_table.insertRow(r)
            for c, v in enumerate([e["spent_at"], e["description"], e["category"], money(e["amount"])]):
                self.exp_table.setItem(r, c, QTableWidgetItem(str(v)))

    def add_expense(self):
        if not self.exp_desc.text().strip() or self.exp_val.value() <= 0:
            QMessageBox.warning(self, "Dados", "Preencha descrição e valor.")
            return
        if QMessageBox.question(
            self, "Confirmar despesa",
            f"Registrar {self.exp_desc.text().strip()} "
            f"({self.exp_cat.currentText()}) no valor de {money(self.exp_val.value())}?"
        ) != QMessageBox.Yes:
            return
        self.db.add_expense(self.exp_desc.text().strip(), self.exp_cat.currentText(),
                            self.exp_val.value())
        self.exp_desc.clear(); self.exp_val.setValue(0)
        self.load_expenses()
        self.update_report()

    # ---------- relatórios ----------
    def _reports_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        top = QHBoxLayout()
        top.addWidget(QLabel("Data:"))
        self.rep_date = QDateEdit(); self.rep_date.setCalendarPopup(True)
        self.rep_date.setDate(date.today())
        top.addWidget(self.rep_date)
        upd = make_button("Atualizar", primary=True); upd.clicked.connect(self.update_report)
        top.addWidget(upd)
        exp = make_button("Exportar PDF", accent=True); exp.clicked.connect(self.export_pdf)
        top.addWidget(exp)
        top.addStretch()
        lay.addLayout(top)

        self.metrics_holder = QWidget()
        self.metrics_layout = QVBoxLayout(self.metrics_holder)
        lay.addWidget(self.metrics_holder)

        self.top_products = QTableWidget(0, 3)
        self.top_products.setHorizontalHeaderLabels(["Produto", "Qtd", "Total"])
        self.top_products.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(QLabel("Top produtos do dia"))
        lay.addWidget(self.top_products)

        self.update_report()
        return w

    def update_report(self):
        while self.metrics_layout.count():
            it = self.metrics_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        day = self.rep_date.date().toString("yyyy-MM-dd") if hasattr(self, "rep_date") else date.today().isoformat()
        data = self.db.report(day)
        grid = QGridLayout()
        cards = [
            ("Faturamento", money(data["total"])),
            ("Pedidos", str(data["count"])),
            ("CMV (custo)", money(data["cost"])),
            ("Despesas", money(data["expenses"])),
            ("Lucro do dia", money(data["profit"])),
            ("Fiados", money(data["pendura"])),
        ]
        for col, (lbl, val) in enumerate(cards):
            card = QFrame(); card.setObjectName("Metric")
            cl = QVBoxLayout(card)
            l1 = QLabel(lbl); l1.setObjectName("MetricLabel")
            cl.addWidget(l1)
            v = QLabel(val); v.setObjectName("MetricValue")
            cl.addWidget(v)
            grid.addWidget(card, 0, col)
        holder = QWidget(); holder.setLayout(grid)
        self.metrics_layout.addWidget(holder)

        methods = data["methods"]
        info = QLabel(
            "  •  ".join([f"{k}: {money(v)}" for k, v in methods.items()]) or "Sem pagamentos."
        )
        info.setStyleSheet("color:#8a6a4f;padding:8px;font-weight:700;")
        self.metrics_layout.addWidget(info)

        if hasattr(self, "top_products"):
            self.top_products.setRowCount(0)
            for p in self.db.top_products(day):
                r = self.top_products.rowCount(); self.top_products.insertRow(r)
                for c, v in enumerate([p["product_name"], p["qty"], money(p["total"])]):
                    self.top_products.setItem(r, c, QTableWidgetItem(str(v)))

    def export_pdf(self):
        day = self.rep_date.date().toString("yyyy-MM-dd")
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar relatório PDF", f"cantina_{day}.pdf", "PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        data = self.db.report(day)
        tops = self.db.top_products(day)
        orders = [o for o in self.db.orders() if o["created_at"].startswith(day)]

        html = f"""
        <html><head><meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; color:#2a1a0f; }}
            h1 {{ color:#d62300; border-bottom:3px solid #d62300; padding-bottom:6px; }}
            h2 {{ color:#d62300; margin-top:24px; }}
            table {{ width:100%; border-collapse:collapse; margin-top:8px; }}
            th, td {{ border:1px solid #f0d9bf; padding:6px 8px; text-align:left; font-size:12px; }}
            th {{ background:#d62300; color:white; }}
            .kpi {{ display:inline-block; margin:6px 12px 6px 0; padding:10px 14px;
                    background:#fff2e6; border-radius:8px; }}
            .kpi b {{ color:#d62300; font-size:16px; }}
            .small {{ color:#8a6a4f; font-size:11px; }}
        </style></head><body>
        <h1>Cantina+ — Relatório de {day}</h1>
        <div>
            <span class="kpi">Faturamento<br><b>{money(data['total'])}</b></span>
            <span class="kpi">Pedidos<br><b>{data['count']}</b></span>
            <span class="kpi">CMV<br><b>{money(data['cost'])}</b></span>
            <span class="kpi">Despesas<br><b>{money(data['expenses'])}</b></span>
            <span class="kpi">Lucro<br><b>{money(data['profit'])}</b></span>
            <span class="kpi">Fiados<br><b>{money(data['pendura'])}</b></span>
        </div>
        <h2>Pagamentos por método</h2>
        <table><tr><th>Método</th><th>Total</th></tr>
        """
        for k, v in data["methods"].items():
            html += f"<tr><td>{k}</td><td>{money(v)}</td></tr>"
        if not data["methods"]:
            html += "<tr><td colspan='2'>Sem pagamentos.</td></tr>"
        html += "</table>"

        html += "<h2>Top produtos do dia</h2><table>"
        html += "<tr><th>Produto</th><th>Qtd</th><th>Total</th></tr>"
        for p in tops:
            html += f"<tr><td>{p['product_name']}</td><td>{p['qty']}</td><td>{money(p['total'])}</td></tr>"
        if not tops:
            html += "<tr><td colspan='3'>Sem vendas.</td></tr>"
        html += "</table>"

        html += "<h2>Pedidos do dia</h2><table>"
        html += ("<tr><th>Senha</th><th>Aluno</th><th>Turma</th><th>Pagamento</th>"
                 "<th>Status Pgto</th><th>Total</th><th>Status</th></tr>")
        for o in orders:
            html += (f"<tr><td>{o['order_number']}</td><td>{o['student_name']}</td>"
                     f"<td>{o['class_name']}</td><td>{o['payment_method']}</td>"
                     f"<td>{o['payment_status']}</td><td>{money(o['total'])}</td>"
                     f"<td>{o['status']}</td></tr>")
        if not orders:
            html += "<tr><td colspan='7'>Sem pedidos.</td></tr>"
        html += "</table>"
        html += f"<p class='small'>Gerado em {date.today().isoformat()} — Cantina+</p></body></html>"

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPageSize(QPageSize.A4))

        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)

        QMessageBox.information(self, "Exportado", f"Relatório PDF salvo em:\n{path}")

    # ---------- segurança ----------
    def _security_tab(self):
        w = QWidget()
        form = QFormLayout(w)
        self.pwd_current = QLineEdit(); self.pwd_current.setEchoMode(QLineEdit.Password)
        self.pwd_new = QLineEdit();     self.pwd_new.setEchoMode(QLineEdit.Password)
        self.pwd_confirm = QLineEdit(); self.pwd_confirm.setEchoMode(QLineEdit.Password)
        form.addRow("Senha atual", self.pwd_current)
        form.addRow("Nova senha", self.pwd_new)
        form.addRow("Confirmar nova senha", self.pwd_confirm)
        save = make_button("Alterar senha", primary=True)
        save.clicked.connect(self.change_password)
        form.addRow("", save)
        return w

    def change_password(self):
        if not self.db.check_admin_password(self.pwd_current.text()):
            QMessageBox.warning(self, "Erro", "Senha atual incorreta.")
            return
        if len(self.pwd_new.text()) < 4:
            QMessageBox.warning(self, "Erro", "A nova senha deve ter ao menos 4 caracteres.")
            return
        if self.pwd_new.text() != self.pwd_confirm.text():
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return
        if QMessageBox.question(self, "Confirmar", "Alterar a senha do administrador?") != QMessageBox.Yes:
            return
        self.db.change_admin_password(self.pwd_new.text())
        self.pwd_current.clear(); self.pwd_new.clear(); self.pwd_confirm.clear()
        QMessageBox.information(self, "OK", "Senha alterada com sucesso.")


# ============================================================== LOGIN ADMIN
class LoginDialog(QWidget):
    success = Signal()
    cancel = Signal()

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        card = QFrame(); card.setObjectName("Card")
        card.setFixedWidth(420)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 30, 30, 30)
        cl.setSpacing(10)

        title = QLabel("🔒  Área restrita")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#d62300;")
        title.setAlignment(Qt.AlignCenter)
        cl.addWidget(title)

        sub = QLabel("Acesso exclusivo para gestores da cantina")
        sub.setStyleSheet("color:#8a6a4f;")
        sub.setAlignment(Qt.AlignCenter)
        cl.addWidget(sub)

        cl.addSpacing(15)
        cl.addWidget(QLabel("Senha:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Digite a senha de administrador")
        self.password.returnPressed.connect(self.try_login)
        cl.addWidget(self.password)
        cl.addSpacing(10)

        enter = make_button("Entrar", primary=True)
        enter.setMinimumHeight(46)
        enter.clicked.connect(self.try_login)
        cl.addWidget(enter)

        lay.addWidget(card, alignment=Qt.AlignCenter)

    def try_login(self) -> None:
        if self.db.check_admin_password(self.password.text()):
            self.password.clear()
            self.success.emit()
        else:
            QMessageBox.warning(self, "Senha incorreta",
                                "Senha de administrador inválida. Tente novamente.")
            self.password.clear()
            self.password.setFocus()


# ============================================================== JANELA
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("Cantina+ 2.0 • Autoatendimento escolar")
        self.resize(1360, 840)
        self.setMinimumSize(1100, 700)

        central = QWidget(); root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0); self.setCentralWidget(central)

        header = QFrame(); header.setObjectName("Header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 14, 20, 14)

        brand_box = QVBoxLayout()
        brand = QLabel("🍔 Cantina+"); brand.setObjectName("Brand")
        sub = QLabel("Autoatendimento escolar"); sub.setObjectName("SubBrand")
        brand_box.addWidget(brand); brand_box.addWidget(sub)
        hl.addLayout(brand_box)
        hl.addStretch()

        self.pages = QStackedWidget()
        self.account = AccountPage(self.db)
        self.kiosk = KioskPage(self.db)
        self.payment = PaymentPage(self.db, self.kiosk)
        self.success = SuccessPage()
        self.kitchen = KitchenPage(self.db)
        self.login = LoginDialog(self.db)
        self.admin = AdminPage(self.db)

        # --- botões do header ---
        self.b_cliente = make_button("🛒  Cliente")
        self.b_cliente.clicked.connect(self._go_cliente)
        hl.addWidget(self.b_cliente)

        self.b_cozinha = make_button("🍳  Cozinha")
        self.b_cozinha.clicked.connect(lambda: self.pages.setCurrentWidget(self.kitchen))
        hl.addWidget(self.b_cozinha)

        self.b_admin = make_button("📊  Admin")
        self.b_admin.clicked.connect(self._go_admin)
        hl.addWidget(self.b_admin)

        for p in [self.account, self.kiosk, self.payment, self.success,
                  self.kitchen, self.login, self.admin]:
            self.pages.addWidget(p)
        root.addWidget(header); root.addWidget(self.pages)

        # --- sinais ---
        self.account.logged.connect(self.on_logged)
        self.kiosk.go_payment.connect(self.show_payment)
        self.kiosk.go_account.connect(self.logout_to_account)
        self.kiosk.go_pay_fiado.connect(self.show_pay_fiado)
        self.payment.back.connect(lambda: self.pages.setCurrentWidget(self.kiosk))
        self.payment.paid.connect(self.show_success)
        self.success.back_home.connect(self.new_order)
        self.login.success.connect(self._on_admin_ok)
        self.login.cancel.connect(self._on_admin_cancel)
        self.pages.currentChanged.connect(self._on_page_changed)

        self.pages.setCurrentWidget(self.account)
        self._refresh_header()

    # -------------------------------------------------- header
    def _refresh_header(self):
        """Define quais botões do header ficam habilitados, com base na tela atual."""
        current = self.pages.currentWidget()

        # tela de login do cliente → só Admin habilitado
        if current is self.account:
            self.b_cliente.setEnabled(False)
            self.b_cozinha.setEnabled(False)
            self.b_admin.setEnabled(True)

        # tela de login do admin → só Cliente habilitado
        elif current is self.login:
            self.b_cliente.setEnabled(True)
            self.b_cozinha.setEnabled(False)
            self.b_admin.setEnabled(False)

        # outras telas → tudo habilitado
        else:
            self.b_cliente.setEnabled(True)
            self.b_cozinha.setEnabled(True)
            self.b_admin.setEnabled(True)

    def _on_page_changed(self, _index):
        self._refresh_header()

    # -------------------------------------------------- troca de contexto
    def _go_cliente(self):
        """Botão Cliente: SEMPRE desloga a sessão atual (seja de admin ou de cliente)
        e vai pra tela de login do cliente."""
        self.kiosk.student = None
        self.kiosk.user_label.setText("Nenhum aluno conectado")
        self.kiosk.pendura_label.setText("")
        self.kiosk.b_fiado.setEnabled(False)
        self.kiosk.b_fiado.setText("💰 Pagar fiado")
        self.kiosk.clear_order()

        self.payment.mode = "order"
        self.payment.chosen_method = None
        self.payment.card_kind = None
        self.payment.stack.setCurrentIndex(0)

        self.account.reset()
        self.pages.setCurrentWidget(self.account)

    def _go_admin(self):
        """Botão Admin: SEMPRE desloga a sessão atual (seja de admin ou de cliente)
        e vai pra tela de login do admin."""
        self.kiosk.student = None
        self.kiosk.user_label.setText("Nenhum aluno conectado")
        self.kiosk.pendura_label.setText("")
        self.kiosk.b_fiado.setEnabled(False)
        self.kiosk.b_fiado.setText("💰 Pagar fiado")
        self.kiosk.clear_order()

        self.payment.mode = "order"
        self.payment.chosen_method = None
        self.payment.card_kind = None
        self.payment.stack.setCurrentIndex(0)

        self.login.password.clear()
        self.pages.setCurrentWidget(self.login)

    # -------------------------------------------------- fluxos
    def on_logged(self, student: dict):
        self.kiosk.set_student(student)
        self.pages.setCurrentWidget(self.kiosk)

    def logout_to_account(self):
        """Usado pelo 'Trocar aluno'."""
        self._go_cliente()

    def show_payment(self):
        self.payment.prepare()
        self.pages.setCurrentWidget(self.payment)

    def show_pay_fiado(self):
        self.payment.prepare_fiado()
        self.pages.setCurrentWidget(self.payment)

    def show_success(self, number):
        total = sum(i["price"] * i["quantity"] for i in self.kiosk.cart)
        self.success.set_number(number, total)
        self.kitchen.refresh()
        self.admin.update_report()
        self.admin.load_penduras()
        self.pages.setCurrentWidget(self.success)

    def new_order(self):
        self._go_cliente()

    def _on_admin_ok(self):
        self.pages.setCurrentWidget(self.admin)

    def _on_admin_cancel(self):
        # cancelou o login admin → volta pra tela de login do cliente
        self._go_cliente()

    def closeEvent(self, event):
        self.db.close(); event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()